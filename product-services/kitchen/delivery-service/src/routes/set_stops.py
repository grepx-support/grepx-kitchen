# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_STOPS - the stops in a new order, with some added or removed; visited stops stay as they were."""
from grepx_service import RequestContext, state_of

from domain import OPEN_STOPS
from dto import RunState
from .common import run_action


def handle(ctx: RequestContext) -> None:
    def body(fleet):
        run = fleet.run((RunState.PLANNED.value, RunState.ON_ROAD.value))
        visited = [s for s in run["stops"] if s["state"] not in OPEN_STOPS]
        wanted = [d for d in ctx.get("delivery_ids") or [] if d not in {s["stop_id"] for s in visited}]
        keep = {s["stop_id"]: s for s in run["stops"] if s["state"] in OPEN_STOPS}
        return fleet.save({**state_of(run), "stops": visited + fleet.stops_for(wanted, run["_key"], keep)})
    run_action(ctx, body)
