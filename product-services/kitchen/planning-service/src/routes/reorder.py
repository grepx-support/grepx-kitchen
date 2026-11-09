# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REORDER - order recommendation per supplier from weekly usage, next to the previous one (R6, ORD-02, ORD-04)."""
from collections import defaultdict

import grepx_contracts as gc
from grepx_service import RequestContext

from domain import reorder
from dto import PlanKind, ReasonCode, Table
from .common import Stop, run, total


def handle(ctx: RequestContext) -> None:
    def body(view):
        place = view.location()
        if not place.get("holding"):
            raise Stop(ReasonCode.NOT_HOLDING_LOCATION)
        on_order: dict[str, float] = defaultdict(float)
        for po in ctx.read.accepted(gc.purchase.PURCHASE_ORDERS, tenant_id=view.tenant):
            if po.get("state") == gc.purchase.PoState.SAVED.value:
                for line in po.get("lines") or []:
                    on_order[line["item_id"]] += float(line.get("qty") or 0)
        today = view.today().isoformat()
        prefix = f"{PlanKind.REORDER.value}:{view.tenant}:{place['_key']}:"
        history = sorted((r for r in ctx.read.accepted(Table.PLANS.value, tenant_id=view.tenant, kind=PlanKind.REORDER.value)
                          if r["_key"].startswith(prefix) and r.get("date", "") < today), key=lambda r: r.get("date", ""))
        previous = (history[-1].get("recommended") if history else None) or {}
        items = view.items(gc.item.ItemKind.INGREDIENT.value, gc.item.ItemKind.SUPPLY.value)
        result = reorder(items, view.usage(), total(view.stock()), dict(on_order), view.safety(), previous,
                         float(view.settings.get("large_change_pct", 30)))
        ctx.emitter.submit(Table.PLANS.value, prefix + today, "ACCEPTED",
                           {"tenant_id": view.tenant, "kind": PlanKind.REORDER.value, "date": today, "location_id": place["_key"],
                            "recommended": {l["item_id"]: l["recommended"] for l in result["lines"]}})
        return {**result, "location_id": place["_key"], "previous_date": history[-1].get("date") if history else None}
    run(ctx, body)
