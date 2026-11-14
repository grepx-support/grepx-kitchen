# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""START_RUN - the van leaves; arrival estimates count from now."""
from grepx_service import RequestContext, state_of

from dto import RunState
from .common import run_action, stamp


def handle(ctx: RequestContext) -> None:
    def body(fleet):
        run = fleet.run((RunState.PLANNED.value,))
        return fleet.save({**state_of(run), "state": RunState.ON_ROAD.value, "started_at": stamp()})
    run_action(ctx, body)
