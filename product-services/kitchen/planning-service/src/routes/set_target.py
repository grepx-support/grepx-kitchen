# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_TARGET - a target typed by hand for the week (no history yet, KIT-10) or extra for an event week (Q12)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import week_start
from dto import PlanKind, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(view):
        item = ctx.read.accepted_one(gc.item.ITEMS, ctx.text("item_id"))
        if item is None or item.get("tenant_id") != view.tenant or item.get("kind") != gc.item.ItemKind.FINISHED.value:
            raise Stop(ReasonCode.UNKNOWN_ITEM)
        values = {}
        for field in ("qty", "extra"):
            value = ctx.get(field)
            if value in (None, ""):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                raise Stop(ReasonCode.INVALID_QUANTITY)
            if number < 0:
                raise Stop(ReasonCode.INVALID_QUANTITY)
            values[field] = int(number) if number.is_integer() else number
        week = week_start(view.today()).isoformat()
        key = f"{PlanKind.TARGET.value}:{view.tenant}:{week}"
        plan = ctx.read.accepted_one(Table.PLANS.value, key) or {}
        items = dict(plan.get("items") or {})
        if values:
            items[item["_key"]] = values
        else:
            items.pop(item["_key"], None)                # nothing sent: back to the calculated target
        row = {"tenant_id": view.tenant, "kind": PlanKind.TARGET.value, "week": week, "items": items, "updated_by": ctx.text("actor_name")}
        ctx.emitter.submit(Table.PLANS.value, key, "ACCEPTED", row)
        return row
    run(ctx, body)
