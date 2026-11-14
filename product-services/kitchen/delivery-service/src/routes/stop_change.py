# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ARRIVE, DELIVER and FAIL_STOP share this: find the stop, check the move, stamp it, close the run when all are done."""
from __future__ import annotations

from grepx_service import state_of

from domain import finished, may_move
from dto import ReasonCode, RunState
from .common import Stop, stamp


def change(fleet, to: str, extra: dict) -> tuple[dict, dict]:
    run = fleet.run((RunState.ON_ROAD.value,))
    stops = [dict(s) for s in run["stops"]]
    stop = next((s for s in stops if s["stop_id"] == fleet.ctx.text("stop_id")), None)
    if stop is None:
        raise Stop(ReasonCode.UNKNOWN_STOP)
    if not may_move(stop, to):
        raise Stop(ReasonCode.WRONG_STATE)
    stop.update({"state": to, f"{to}_at": stamp(), **extra})
    run = {**state_of(run), "stops": stops}
    if finished(stops):
        run.update({"state": RunState.DONE.value, "finished_at": stamp()})
    return run, stop
