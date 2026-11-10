# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Inventory control: alerts, par levels, stock takes, valuation and analysis. Rules live in inventory-service."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.views import clean
from kitchen import Kitchen, allow, listed

router = APIRouter(prefix="/inventory", tags=["inventory"])
LOOK = allow("view_stock", "manage_business", module="inventory")
COUNT = allow("adjust_stock", "manage_business", module="inventory")


def cmd(k: Kitchen, fields: dict) -> dict:
    return k.cmd(gc.inventory.REQUESTS, gc.inventory.SERVICE, fields)


@router.get("/alerts")
def alerts(k: Kitchen = Depends(LOOK)):
    rows = [clean(a) for a in k.rows(gc.inventory.ALERTS) if a.get("state") == "open"]
    return {"alerts": sorted(rows, key=lambda a: ({"expired": 0, "negative": 1, "expiring": 2, "low": 3}.get(a["kind"], 9), a.get("item_name", "")))}


@router.post("/alerts/check")
def check(k: Kitchen = Depends(LOOK)):
    return cmd(k, {"action": "CHECK_ALERTS"})


@router.post("/alerts/{alert_id}/done")
def done(alert_id: str, k: Kitchen = Depends(LOOK)):
    return cmd(k, {"action": "ACK_ALERT", "alert_id": alert_id})["alert"]


@router.get("/par")
def par(location_id: str = "", k: Kitchen = Depends(LOOK)):
    places = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}
    place = location_id or next(iter(places), "")
    levels = {p["item_id"]: p for p in k.rows(gc.inventory.PAR_LEVELS, location_id=place)}
    held = {l["item_id"]: l.get("qty", 0) for l in k.rows(gc.stock.STOCK_LEVELS, location_id=place)}
    items = listed([clean(i) for i in k.rows(gc.item.ITEMS) if i.get("active", True)], "name")
    return {"location_id": place, "lines": [{"item_id": i["id"], "name": i["name"], "unit": i["unit"], "on_hand": held.get(i["id"], 0),
                                             "min": levels.get(i["id"], {}).get("min"), "max": levels.get(i["id"], {}).get("max")} for i in items]}


@router.post("/par")
def set_par(body: dict, k: Kitchen = Depends(allow("manage_business", "warehouse_in", module="inventory"))):
    return cmd(k, {"action": "SET_PAR", **{f: body.get(f) for f in ("location_id", "item_id", "min", "max")}})["par"]


@router.get("/takes")
def takes(k: Kitchen = Depends(COUNT)):
    rows = sorted((clean(t) for t in k.rows(gc.inventory.STOCK_TAKES)), key=lambda t: t.get("started_at", ""), reverse=True)
    return {"takes": rows[:30]}


@router.post("/takes")
def start(body: dict, k: Kitchen = Depends(COUNT)):
    return cmd(k, {"action": "START_TAKE", "location_id": body.get("location_id"), "blind": bool(body.get("blind")),
                   "all_items": bool(body.get("all_items"))})["take"]


@router.post("/takes/{take_id}/count")
def count(take_id: str, body: dict, k: Kitchen = Depends(COUNT)):
    return cmd(k, {"action": "COUNT_TAKE", "take_id": take_id, "lines": body.get("lines") or []})["take"]


@router.post("/takes/{take_id}/{verb}")
def finish(take_id: str, verb: str, k: Kitchen = Depends(COUNT)):
    from grepx_bff.errors import ApiError
    action = {"finish": "FINISH_TAKE", "cancel": "CANCEL_TAKE"}.get(verb)
    if action is None:
        raise ApiError("NOT_FOUND", 404)
    return cmd(k, {"action": action, "take_id": take_id})["take"]


@router.get("/valuation")
def valuation(location_id: str = "", k: Kitchen = Depends(allow("view_costs", "manage_business", module="inventory"))):
    out = cmd(k, {"action": "VALUATION", "location_id": location_id})
    items, places = k.items(), {r["_key"]: r.get("name", "") for r in k.rows(gc.business.LOCATIONS)}
    return {"total": out["total"], "lot_total": out["lot_total"],
            "lines": [{**l, "name": items.get(l["item_id"], {}).get("name", ""), "unit": items.get(l["item_id"], {}).get("unit", ""),
                       "location_name": places.get(l["location_id"], "")} for l in out["lines"]]}


@router.get("/analysis")
def analysis(days: int = 30, k: Kitchen = Depends(LOOK)):
    out = cmd(k, {"action": "ANALYSIS", "days": days})
    return {"days": out["days"], "since": out["since"], "items": out["items"], "waste": out["waste"]}
