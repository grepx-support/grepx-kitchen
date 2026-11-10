# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COMPLETE_PICK - everything picked is sent: one stock-service SEND (warehouse-out) with what was picked."""
import grepx_contracts as gc
from grepx_service import RequestContext, now_iso, state_of

from dto import PickState, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        pick = floor.mine(Table.PICKS.value, ctx.text("pick_id"), ReasonCode.UNKNOWN_PICK)
        if pick.get("state") != PickState.OPEN.value:
            raise Stop(ReasonCode.PICK_CLOSED)
        lines = [{"item_id": l["item_id"], "qty": l["picked"], **({"lot_id": l["lots"][0]["lot_id"]} if l.get("lots") else {})}
                 for l in pick["lines"] if l.get("picked", 0) > 0]
        if not lines:
            raise Stop(ReasonCode.NOTHING_PICKED)
        ctx.request(gc.stock.REQUESTS, f"pick-{pick['_key']}",
                    {"action": gc.stock.StockAction.SEND.value, "tenant_id": floor.tenant, "from_location_id": pick["from_location_id"],
                     "to_location_id": pick["to_location_id"], "lines": lines, "ref": pick["_key"], "note": "Pick list",
                     "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.stock.SERVICE)
        done = {**state_of(pick), "state": PickState.DONE.value, "done_at": now_iso(), "done_by_name": ctx.text("actor_name")}
        return {"pick": floor.save(Table.PICKS.value, pick["_key"], done)}
    run(ctx, body)
