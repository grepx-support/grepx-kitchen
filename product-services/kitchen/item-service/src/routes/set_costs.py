# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_COSTS - new costs for several items at once ({item_id: cost}), e.g. what they really cost on an approved
supplier bill with its landed costs. Unknown items are skipped; each change is kept in the item's cost history."""
from grepx_service import RequestContext, now_iso, state_of

from domain.costs import recost
from dto import Table
from .common import guard, mine


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    changed, at = [], now_iso()
    try:
        for item_id, cost in (ctx.get("costs") or {}).items():
            row = mine(ctx, Table.ITEMS.value, item_id, tenant)
            if row is None:
                continue
            item = state_of(row)
            new = recost(item, cost, ctx.text("source") or "Cost update", at)
            if new is not item:
                ctx.emitter.submit(Table.ITEMS.value, item_id, "ACCEPTED", new)
                changed.append({"item_id": item_id, "name": item.get("name", ""), "was": item.get("cost"), "cost": new["cost"]})
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept({"changed": changed})
