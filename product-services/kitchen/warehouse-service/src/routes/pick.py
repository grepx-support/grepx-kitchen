# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PICK - how much of one line was picked (0 to undo)."""
from grepx_service import RequestContext, state_of

from dto import PickState, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        pick = floor.mine(Table.PICKS.value, ctx.text("pick_id"), ReasonCode.UNKNOWN_PICK)
        if pick.get("state") != PickState.OPEN.value:
            raise Stop(ReasonCode.PICK_CLOSED)
        try:
            qty = float(ctx.get("qty"))
        except (TypeError, ValueError):
            raise Stop(ReasonCode.INVALID_QUANTITY)
        if qty < 0:
            raise Stop(ReasonCode.INVALID_QUANTITY)
        lines = [dict(l) for l in pick["lines"]]
        line = next((l for l in lines if l["item_id"] == ctx.text("item_id")), None)
        if line is None:
            raise Stop(ReasonCode.UNKNOWN_ITEM)
        line["picked"] = round(qty, 4)
        return {"pick": floor.save(Table.PICKS.value, pick["_key"], {**state_of(pick), "lines": lines})}
    run(ctx, body)
