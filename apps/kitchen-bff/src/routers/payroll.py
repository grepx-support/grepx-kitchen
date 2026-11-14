# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Payroll (payroll-service): the country and its rates in one place, the month's run, bonuses / advances, locking
the month - which also puts each outlet's labour cost (pay + employer contributions) into Costs for that month."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/payroll", tags=["payroll"])
owner = allow("manage_business")          # pay is the owner's business; outlet managers do not see it


def ask(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.payroll.REQUESTS, gc.payroll.SERVICE, {"action": action, **fields})


@router.get("/settings")
def settings(k: Kitchen = Depends(owner)):
    return ask(k, "SETTINGS")


@router.put("/settings")
def set_settings(body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "SET_SETTINGS", country=body.get("country", ""), rates=body.get("rates") or {})["settings"]


@router.get("")
def month(month: str, k: Kitchen = Depends(owner)):
    return ask(k, "MONTH", month=month)


@router.post("/run")
def run(body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "RUN", month=body.get("month"))["run"]


@router.post("/adjust")
def adjust(body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "ADJUST", **{f: body.get(f) for f in ("month", "employee_id", "kind", "amount", "note")})["adjustment"]


@router.delete("/adjust/{adjustment_id}")
def remove(adjustment_id: str, k: Kitchen = Depends(owner)):
    return ask(k, "REMOVE_ADJUSTMENT", adjustment_id=adjustment_id)


@router.post("/finalise")
def finalise(body: dict, k: Kitchen = Depends(owner)):
    """Lock the month, then set each outlet's labour cost for it (rent and other costs stay as they were)."""
    m = body.get("month")
    done = ask(k, "FINALISE", month=m)
    places = {r["_key"] for r in k.rows(gc.business.LOCATIONS)}
    for site, cost in done["cost_by_site"].items():
        if site not in places:
            continue
        now = next(iter(k.rows(gc.costing.OVERHEADS, location_id=site, month=m)), {})
        k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SET_OVERHEAD", "location_id": site, "month": m, "labour": cost,
                                                        "rent": now.get("rent", 0), "other": now.get("other", 0)})
    return done
