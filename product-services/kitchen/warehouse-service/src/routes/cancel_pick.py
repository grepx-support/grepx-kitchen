# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CANCEL_PICK - drop an open pick list; nothing moves."""
from grepx_service import RequestContext, state_of

from dto import PickState, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        pick = floor.mine(Table.PICKS.value, ctx.text("pick_id"), ReasonCode.UNKNOWN_PICK)
        if pick.get("state") != PickState.OPEN.value:
            raise Stop(ReasonCode.PICK_CLOSED)
        return {"pick": floor.save(Table.PICKS.value, pick["_key"], {**state_of(pick), "state": PickState.CANCELLED.value})}
    run(ctx, body)
