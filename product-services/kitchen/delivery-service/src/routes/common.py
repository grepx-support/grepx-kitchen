# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every run action shares: the business, its runs, the warehouse-out trips stops are made of."""
from __future__ import annotations

from datetime import datetime, timezone

import grepx_contracts as gc
from grepx_service import RequestContext, state_of

from domain import OPEN_STOPS, eta
from dto import ReasonCode, RunState, Table


class Stop(Exception):
    """A rejection with its reason."""


class Fleet:
    def __init__(self, ctx: RequestContext):
        self.ctx = ctx
        self.tenant = ctx.text("tenant_id")
        if not self.tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        if ctx.read.accepted_one(gc.business.BUSINESSES, self.tenant) is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)

    def run(self, states: tuple = ()) -> dict:
        row = self.ctx.read.accepted_one(Table.RUNS.value, self.ctx.text("run_id"))
        if row is None or row.get("tenant_id") != self.tenant:
            raise Stop(ReasonCode.UNKNOWN_RUN)
        if states and row.get("state") not in states:
            raise Stop(ReasonCode.WRONG_STATE)
        return row

    def stops_for(self, delivery_ids, run_id: str = "", keep: dict | None = None) -> list[dict]:
        """Stops for these warehouse-out trips (still to deliver, not on another open run); known stops keep their state."""
        keep = keep or {}
        busy = {s["stop_id"] for r in self.ctx.read.accepted(Table.RUNS.value, tenant_id=self.tenant)
                if r["_key"] != run_id and r.get("state") in (RunState.PLANNED.value, RunState.ON_ROAD.value)
                for s in r.get("stops") or [] if s["state"] in OPEN_STOPS}
        out = []
        for did in dict.fromkeys(str(d) for d in delivery_ids or []):
            if did in keep:
                out.append(keep[did])
                continue
            trip = self.ctx.read.accepted_one(gc.stock.DELIVERIES, did)
            if trip is None or trip.get("tenant_id") != self.tenant:
                raise Stop(ReasonCode.UNKNOWN_DELIVERY)
            if trip.get("state") == "delivered":
                raise Stop(ReasonCode.ALREADY_DELIVERED)
            if did in busy:
                raise Stop(ReasonCode.ON_ANOTHER_RUN)
            place = self.ctx.read.accepted_one(gc.business.LOCATIONS, trip.get("to_location_id", "")) or {}
            out.append({"stop_id": did, "delivery_id": did, "location_id": trip.get("to_location_id", ""), "name": place.get("name", ""),
                        "address": place.get("address", ""), "lines": trip.get("lines", 0), "state": "pending"})
        if not out:
            raise Stop(ReasonCode.NO_STOPS)
        return out

    def save(self, run: dict) -> dict:
        now = datetime.now() if run.get("state") == RunState.ON_ROAD.value else None
        run = {**run, "stops": eta(run, run["stops"], now)}
        self.ctx.emitter.submit(Table.RUNS.value, run["run_id"], "ACCEPTED", run)
        return run


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_action(ctx: RequestContext, body) -> None:
    try:
        out = body(Fleet(ctx))
    except Stop as stop:
        return ctx.reject(stop.args[0])
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept({"run": out})


__all__ = ["Fleet", "Stop", "run_action", "stamp", "state_of"]
