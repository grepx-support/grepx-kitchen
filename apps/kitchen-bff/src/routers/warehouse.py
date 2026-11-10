# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The warehouse floor: bins, lots with expiry (first expiry first out), pick lists that become a warehouse-out.
Rules live in warehouse-service; this only shapes them for the screens."""
from datetime import date

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.views import clean
from kitchen import Kitchen, allow, listed

router = APIRouter(prefix="/warehouse", tags=["warehouse"])
FLOOR = allow("warehouse_in", "warehouse_out", "view_stock", module="inventory")
PICKER = allow("warehouse_out", module="inventory")


def cmd(k: Kitchen, fields: dict) -> dict:
    return k.cmd(gc.warehouse.REQUESTS, gc.warehouse.SERVICE, fields)


@router.get("")
def floor(location_id: str = "", k: Kitchen = Depends(FLOOR)):
    """Bins and open lots of one location (the holding place when none is given), soonest expiry first."""
    places = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}
    place = location_id or next((key for key, p in places.items() if p.get("holding")), "")
    items, today = k.items(), date.today()
    bins = {b["_key"]: clean(b) for b in k.rows(gc.warehouse.BINS, location_id=place)}
    lots = []
    for lot in k.rows(gc.warehouse.LOTS, location_id=place):
        if lot.get("qty", 0) <= 0:
            continue
        item = items.get(lot["item_id"], {})
        left = (date.fromisoformat(lot["expiry"]) - today).days if lot.get("expiry") else None
        lots.append({**clean(lot), "item_name": item.get("name", lot["item_id"]), "unit": item.get("unit", ""), "days_left": left,
                     "bin_code": bins.get(lot.get("bin_id", ""), {}).get("code", "")})
    lots.sort(key=lambda l: (l["days_left"] is None, l["days_left"] or 0, l["item_name"]))
    picks = [clean(p) for p in k.rows(gc.warehouse.PICKS, state="open") if p.get("from_location_id") == place]
    return {"location_id": place, "bins": listed(list(bins.values()), "code"), "lots": lots, "picks": picks,
            "places": {key: p.get("name", "") for key, p in places.items()}}


@router.post("/bins")
def save_bin(body: dict, k: Kitchen = Depends(allow("warehouse_in", "manage_business", module="inventory"))):
    return cmd(k, {"action": "SAVE_BIN", **{f: body.get(f) for f in ("bin_id", "location_id", "code", "zone", "note", "active")}})["bin"]


@router.post("/lots/{lot_id}/move")
def move_lot(lot_id: str, body: dict, k: Kitchen = Depends(allow("warehouse_in", "warehouse_out", module="inventory"))):
    return cmd(k, {"action": "MOVE_LOT", "lot_id": lot_id, "bin_id": body.get("bin_id", "")})["lot"]


@router.post("/picks")
def create_pick(body: dict, k: Kitchen = Depends(PICKER)):
    return cmd(k, {"action": "CREATE_PICK", "from_location_id": body.get("from_location_id"), "to_location_id": body.get("to_location_id"),
                   "lines": [{"item_id": l.get("item_id"), "qty": l.get("qty")} for l in body.get("lines") or []]})["pick"]


@router.get("/picks/{pick_id}")
def pick_list(pick_id: str, k: Kitchen = Depends(PICKER)):
    pick = k.one(gc.warehouse.PICKS, pick_id)
    if pick is None:
        from grepx_bff.errors import ApiError
        raise ApiError("NOT_FOUND", 404)
    bins = {b["_key"]: b.get("code", "") for b in k.rows(gc.warehouse.BINS)}
    places = {r["_key"]: r.get("name", "") for r in k.rows(gc.business.LOCATIONS)}
    lines = [{**l, "lots": [{**x, "bin_code": bins.get(x.get("bin_id", ""), "")} for x in l.get("lots") or []]} for l in pick.get("lines") or []]
    lines.sort(key=lambda l: (l["lots"][0]["bin_code"] if l["lots"] else "~", l.get("name", "")))     # walk the bins in order
    return {**clean(pick), "lines": lines, "from_name": places.get(pick.get("from_location_id"), ""), "to_name": places.get(pick.get("to_location_id"), "")}


@router.post("/picks/{pick_id}/pick")
def pick(pick_id: str, body: dict, k: Kitchen = Depends(PICKER)):
    return cmd(k, {"action": "PICK", "pick_id": pick_id, "item_id": body.get("item_id"), "qty": body.get("qty")})["pick"]


@router.post("/picks/{pick_id}/{verb}")
def finish_pick(pick_id: str, verb: str, k: Kitchen = Depends(PICKER)):
    action = {"complete": "COMPLETE_PICK", "cancel": "CANCEL_PICK"}.get(verb)
    if action is None:
        from grepx_bff.errors import ApiError
        raise ApiError("NOT_FOUND", 404)
    return cmd(k, {"action": action, "pick_id": pick_id})["pick"]
