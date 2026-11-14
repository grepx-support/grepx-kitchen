# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""MOVE_LOT - putaway: put a lot in a bin of the same location (or take it out of any bin with an empty bin_id)."""
from grepx_service import RequestContext, state_of

from dto import ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        lot = floor.mine(Table.LOTS.value, ctx.text("lot_id"), ReasonCode.UNKNOWN_LOT)
        bin_id = ctx.text("bin_id")
        if bin_id and floor.mine(Table.BINS.value, bin_id, ReasonCode.UNKNOWN_BIN).get("location_id") != lot["location_id"]:
            raise Stop(ReasonCode.UNKNOWN_BIN)
        return {"lot": floor.save(Table.LOTS.value, lot["_key"], {**state_of(lot), "bin_id": bin_id})}
    run(ctx, body)
