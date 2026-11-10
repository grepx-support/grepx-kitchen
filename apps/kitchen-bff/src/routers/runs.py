# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Delivery runs: the dispatcher plans a driver's day from warehouse-out trips (drag them in order), the driver works
the run on the phone (arrive, deliver with name and signature, or fail with a reason). Rules live in delivery-service."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.errors import ApiError
from grepx_bff.views import clean
from kitchen import Kitchen, allow

router = APIRouter(prefix="/runs", tags=["runs"])
DISPATCH = allow("warehouse_out", "manage_business", module="inventory")
DRIVER = allow("delivery", "warehouse_out", module="inventory")
OPEN = ("planned", "on_road")


def cmd(k: Kitchen, fields: dict) -> dict:
    return k.cmd(gc.delivery.REQUESTS, gc.delivery.SERVICE, fields)["run"]


@router.get("")
def board(date: str = "", k: Kitchen = Depends(DRIVER)):
    """Runs (of a day, or still open) and the trips not on any open run yet."""
    runs = [clean(r) for r in k.rows(gc.delivery.RUNS) if (r.get("date") == date if date else r.get("state") in OPEN)]
    busy = {s["stop_id"] for r in runs if r["state"] in OPEN for s in r.get("stops") or [] if s["state"] in ("pending", "arrived")}
    places = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}
    waiting = [{"id": t["_key"], "to": places.get(t.get("to_location_id", ""), {}).get("name", ""), "address": places.get(t.get("to_location_id", ""), {}).get("address", ""),
                "date": t.get("date", ""), "lines": t.get("lines", 0), "sent_by": t.get("sent_by", "")}
               for t in k.rows(gc.stock.DELIVERIES, state="sent") if t["_key"] not in busy]
    drivers = [{"id": a["_key"], "name": (k.one(gc.people.PEOPLE, a["_key"]) or {}).get("name", "")}
               for a in k.gw.rows(gc.access.USER_ACCESS) if a.get("staff_role_id") in (f"{k.tenant}.delivery", f"{k.tenant}.owner")]
    return {"runs": sorted(runs, key=lambda r: (r["date"], r.get("start_time", ""))), "waiting": sorted(waiting, key=lambda t: t["date"]),
            "drivers": [d for d in drivers if d["name"]]}


@router.get("/mine")
def mine(k: Kitchen = Depends(DRIVER)):
    """The driver's open runs."""
    return {"runs": [clean(r) for r in k.rows(gc.delivery.RUNS) if r.get("state") in OPEN and r.get("driver_id") == k.user.user_id]}


@router.post("")
def plan(body: dict, k: Kitchen = Depends(DISPATCH)):
    fields = {f: body.get(f) for f in ("date", "start_time", "name", "vehicle", "driver_id", "drive_minutes", "service_minutes", "delivery_ids")}
    if fields.get("driver_id"):
        fields["driver_name"] = (k.one(gc.people.PEOPLE, fields["driver_id"]) or {}).get("name", "")
    return cmd(k, {"action": "PLAN_RUN", **fields})


@router.post("/{run_id}/stops")
def stops(run_id: str, body: dict, k: Kitchen = Depends(DISPATCH)):
    return cmd(k, {"action": "SET_STOPS", "run_id": run_id, "delivery_ids": body.get("delivery_ids") or []})


@router.post("/{run_id}/{verb}")
def run_verb(run_id: str, verb: str, k: Kitchen = Depends(DRIVER)):
    action = {"start": "START_RUN", "cancel": "CANCEL_RUN"}.get(verb)
    if action is None:
        raise ApiError("NOT_FOUND", 404)
    return cmd(k, {"action": action, "run_id": run_id})


@router.post("/{run_id}/stops/{stop_id}/{verb}")
def stop_verb(run_id: str, stop_id: str, verb: str, body: dict | None = None, k: Kitchen = Depends(DRIVER)):
    action = {"arrive": "ARRIVE", "deliver": "DELIVER", "fail": "FAIL_STOP"}.get(verb)
    if action is None:
        raise ApiError("NOT_FOUND", 404)
    body = body or {}
    return cmd(k, {"action": action, "run_id": run_id, "stop_id": stop_id, "receiver": body.get("receiver", ""),
                   "signature": body.get("signature", ""), "note": body.get("note", ""), "reason": body.get("reason", "")})
