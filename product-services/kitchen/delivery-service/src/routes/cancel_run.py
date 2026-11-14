# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CANCEL_RUN - a run that has not left; its trips can be planned again."""
from grepx_service import RequestContext, state_of

from dto import RunState
from .common import run_action


def handle(ctx: RequestContext) -> None:
    def body(fleet):
        run = fleet.run((RunState.PLANNED.value,))
        return fleet.save({**state_of(run), "state": RunState.CANCELLED.value})
    run_action(ctx, body)
