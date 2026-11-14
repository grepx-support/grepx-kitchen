# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Food safety (compliance-service): each place's checks - fridge / freezer / hot-holding temperatures, cooling,
opening and closing checklists - recorded on the day, failures with the action taken, the log for inspectors.
The standard kitchen set of checks can be added to a place in one go."""
from datetime import datetime
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/safety", tags=["safety"])
staff = allow("kitchen", "closing", "manage_people", "manage_business")
manager = allow("manage_people", "manage_business")
POINT = ("point_id", "site_id", "name", "kind", "unit", "min", "max", "questions", "every", "group")

PRESETS = [
    {"name": "Walk-in fridge", "unit": "°C", "min": 0, "max": 5, "every": "twice_daily", "group": "Temperatures"},
    {"name": "Freezer", "unit": "°C", "max": -18, "every": "twice_daily", "group": "Temperatures"},
    {"name": "Hot holding (bain-marie)", "unit": "°C", "min": 63, "every": "twice_daily", "group": "Temperatures"},
    {"name": "Cooked food core temperature", "unit": "°C", "min": 75, "every": "daily", "group": "Cooking & cooling"},
    {"name": "Cooling: below 5°C within 90 min", "unit": "°C", "max": 5, "every": "daily", "group": "Cooking & cooling"},
    {"name": "Delivery received temperature (chilled)", "unit": "°C", "max": 5, "every": "daily", "group": "Deliveries"},
    {"name": "Opening checks", "kind": "checklist", "every": "daily", "group": "Checklists",
     "questions": ["Staff fit to work, hands washed", "Fridges and freezers working", "Surfaces and boards sanitised", "No signs of pests",
               "Hand-wash basins stocked (soap, towels)"]},
    {"name": "Closing checks", "kind": "checklist", "every": "daily", "group": "Checklists",
     "questions": ["Food covered, labelled and dated", "Raw and cooked stored apart", "Floors and drains cleaned", "Waste removed",
               "Equipment switched off / cleaned"]},
    {"name": "Weekly deep clean", "kind": "checklist", "every": "weekly", "group": "Checklists",
     "questions": ["Extraction hood and filters", "Behind and under equipment", "Cold room shelves", "Dry store"]},
]


def ask(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.compliance.REQUESTS, gc.compliance.SERVICE, {"action": action, **fields})


def local_now(k: Kitchen) -> datetime:
    return datetime.now(ZoneInfo(k.business.get("timezone") or "UTC"))


@router.get("/day")
def day(site_id: str = "", date: str = "", k: Kitchen = Depends(staff)):
    return ask(k, "DAY", site_id=site_id, date=date or local_now(k).date().isoformat())


@router.post("/record")
def record(body: dict, k: Kitchen = Depends(staff)):
    return ask(k, "RECORD", **{f: body.get(f) for f in ("point_id", "value", "answers", "action_taken", "note")},
               at=local_now(k).isoformat(timespec="minutes")[:16])["record"]


@router.post("/points")
def save_point(body: dict, k: Kitchen = Depends(manager)):
    return ask(k, "SAVE_POINT", **{f: body.get(f) for f in POINT if body.get(f) is not None})["point"]


@router.delete("/points/{point_id}")
def remove_point(point_id: str, k: Kitchen = Depends(manager)):
    return ask(k, "REMOVE_POINT", point_id=point_id)


@router.post("/presets")
def presets(body: dict, k: Kitchen = Depends(manager)):
    """The standard kitchen checks at one place (those it has by the same name are left alone)."""
    have = {p["name"] for p in ask(k, "DAY", site_id=body.get("site_id"))["points"]}
    added = [ask(k, "SAVE_POINT", site_id=body.get("site_id"), **p)["point"]["name"] for p in PRESETS if p["name"] not in have]
    return {"added": added}


@router.get("/history")
def history(first: str, last: str, site_id: str = "", k: Kitchen = Depends(manager)):
    return ask(k, "HISTORY", first=first, last=last, site_id=site_id)
