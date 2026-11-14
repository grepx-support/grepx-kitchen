# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Stock at each location, its history, and the daily moves: receive, warehouse out (with suggestions), transfer,
adjust (INV-01..11, R1..R4). Delivery staff see only what leaves the warehouse."""
from collections import defaultdict

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.errors import ApiError
from kitchen import Kitchen, allow, listed, named

router = APIRouter(prefix="/stock", tags=["stock"])
INV = "inventory"


LOT_FIELDS = ("expiry", "lot_code", "bin_id", "lot_id")      # optional: warehouse-service files the stock under these lots


def lines(body: dict) -> list[dict]:
    return [{"item_id": l.get("item_id"), "qty": l.get("qty"), **{f: l[f] for f in LOT_FIELDS if l.get(f)}} for l in body.get("lines") or []]


@router.get("")
def levels(location_id: str = "", k: Kitchen = Depends(allow("view_stock", "warehouse_out", "warehouse_in", "transfer", "adjust_stock",
                                                             "kitchen", module=INV))):
    places = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}
    rows = k.rows(gc.stock.STOCK_LEVELS, location_id=location_id) if location_id else k.rows(gc.stock.STOCK_LEVELS)
    return {"levels": sorted(named(rows, k.items(), places), key=lambda r: (r.get("location_name", ""), r["item_name"]))}


@router.get("/items")
def items(k: Kitchen = Depends(allow())):
    """Every active item of the business (name, unit, kind) - for adding a line on any stock screen. No costs here."""
    rows = [r for r in k.rows(gc.item.ITEMS) if r.get("active", True)]
    return {"items": [{"id": r["_key"], "name": r.get("name", ""), "unit": r.get("unit", ""), "kind": r.get("kind", ""),
                       "category": r.get("category", ""), "barcode": r.get("barcode", ""), "price": r.get("price") or 0,
                       "shelf_life_days": r.get("shelf_life_days"), "components": r.get("components") or [],
                       "breaks_into": r.get("breaks_into") or []} for r in listed(rows, "name")]}


@router.get("/movements")
def movements(location_id: str = "", item_id: str = "", limit: int = 200, k: Kitchen = Depends(allow("view_stock", module=INV))):
    """INV-10 / QR-06: the history, newest first; nobody can change it."""
    eq = {f: v for f, v in (("location_id", location_id), ("item_id", item_id)) if v}
    rows = sorted(k.rows(gc.stock.STOCK_MOVEMENTS, **eq), key=lambda r: (r.get("at", ""), r["_key"]), reverse=True)[: max(1, min(limit, 1000))]
    places = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}
    show_cost = k.can("view_costs")
    out = named(rows, k.items(), places)
    if not show_cost:                                     # COS-08: costs only for roles that may see them
        for r in out:
            r.pop("unit_cost", None), r.pop("value", None)
    return {"movements": out}


def plan(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.planning.REQUESTS, gc.planning.SERVICE, {"action": action, **fields})["plan"]


@router.get("/warehouse-out")
def warehouse_out(to_location_id: str, k: Kitchen = Depends(allow("warehouse_out", module=INV))):
    """INV-02/03: the suggested lines; the user accepts all, or changes / removes lines, then sends."""
    return plan(k, "WAREHOUSE_OUT", to_location_id=to_location_id)


@router.get("/warehouse-in")
def warehouse_in(location_id: str, k: Kitchen = Depends(allow("warehouse_in", "orders", module=INV))):
    return plan(k, "WAREHOUSE_IN", location_id=location_id)


@router.post("/send")
def send(body: dict, k: Kitchen = Depends(allow("warehouse_out", module=INV))):
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "SEND", "from_location_id": body.get("from_location_id"),
                                                       "to_location_id": body.get("to_location_id"), "lines": lines(body)})


@router.post("/receive")
def receive(body: dict, k: Kitchen = Depends(allow("warehouse_in", module=INV))):
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "RECEIVE", "location_id": body.get("location_id"), "lines": lines(body),
                                                       "note": body.get("note", "")})


@router.post("/waste")
def waste(body: dict, k: Kitchen = Depends(allow("adjust_stock", "warehouse_in", "kitchen", "closing", module=INV))):
    """Thrown away, with the reason (expired, spoiled, damaged, overproduced, other) - counts in the cost of goods."""
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "WASTE", "location_id": body.get("location_id"), "lines": lines(body),
                                                       "reason": body.get("reason", ""), "note": body.get("note", "")})


@router.post("/break-down")
def break_down(body: dict, k: Kitchen = Depends(allow("adjust_stock", "warehouse_in", "kitchen", module=INV))):
    """Bulk into its parts at one place (a whole chicken into cuts); outputs: what really came out (else the item's own split)."""
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": gc.stock.StockAction.BREAK_DOWN.value, "location_id": body.get("location_id"),
                                                       "lines": lines(body), "outputs": body.get("outputs"), "note": body.get("note", "")})


@router.post("/transfer")
def transfer(body: dict, k: Kitchen = Depends(allow("transfer", module=INV))):
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "TRANSFER", "from_location_id": body.get("from_location_id"),
                                                       "to_location_id": body.get("to_location_id"), "lines": lines(body)})


@router.post("/adjust")
def adjust(body: dict, k: Kitchen = Depends(allow("adjust_stock", module=INV))):
    """INV-08/09, ACC-03: only roles the owner chose; the reason is required."""
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "ADJUST", "location_id": body.get("location_id"), "lines": lines(body),
                                                       "note": body.get("note", "")})


DELIVERY = allow("delivery", "warehouse_out", module=INV)


@router.get("/deliveries")
def deliveries(date: str = "", k: Kitchen = Depends(DELIVERY)):
    """What left the warehouse (by day and destination) - the delivery person's list, never the production plan.
    Each trip is `sent` until the destination confirms it (`delivered`); trips from before tracking show as delivered."""
    rows = [r for r in k.rows(gc.stock.STOCK_MOVEMENTS, kind="send_out") if not date or r.get("date") == date]
    places, items = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}, k.items()
    tracked = {r["_key"]: r for r in k.rows(gc.stock.DELIVERIES)}
    trips: dict = defaultdict(list)
    for r in sorted(rows, key=lambda r: r.get("at", ""), reverse=True)[:500]:
        trips[(r.get("date"), r.get("request_id"))].append(r)
    return {"deliveries": [trip_view(request_id, day, moves, tracked.get(request_id) or {}, places, items) for (day, request_id), moves in trips.items()]}


def trip_view(request_id: str, day: str, moves: list[dict], track: dict, places: dict, items: dict) -> dict:
    first = moves[0]
    return {"id": request_id, "date": day, "at": first.get("at"), "from": places.get(first["location_id"], {}).get("name", ""),
            "to": places.get(first.get("other_location_id", ""), {}).get("name", ""), "by": first.get("user_name", ""),
            "to_address": places.get(first.get("other_location_id", ""), {}).get("address", ""),
            "state": track.get("state", "delivered"), "delivered_by": track.get("delivered_by", ""),
            "delivered_at": track.get("delivered_at", ""), "tracked": bool(track),
            "lines": [{"item_name": items.get(m["item_id"], {}).get("name", m["item_id"]), "unit": items.get(m["item_id"], {}).get("unit", ""),
                       "qty": -m["qty"]} for m in moves]}


def handover(delivery_id: str, k: Kitchen) -> tuple[dict | None, dict | None]:
    """The run stop that delivered this trip (receiver, signatures, time) and its run - (None, None) before that."""
    for r in k.rows(gc.delivery.RUNS):
        for s in r.get("stops") or []:
            if s.get("delivery_id") == delivery_id:
                return s, r
    return None, None


def trip(delivery_id: str, k: Kitchen) -> dict:
    """One trip that left the warehouse (the delivery note's lines)."""
    moves = sorted((r for r in k.rows(gc.stock.STOCK_MOVEMENTS, kind="send_out") if r.get("request_id") == delivery_id), key=lambda r: r.get("at", ""))
    if not moves:
        raise ApiError("UNKNOWN_DELIVERY", 404)
    places = {r["_key"]: r for r in k.rows(gc.business.LOCATIONS)}
    return trip_view(delivery_id, moves[0].get("date", ""), moves, k.one(gc.stock.DELIVERIES, delivery_id) or {}, places, k.items())


@router.post("/deliveries/{delivery_id}/delivered")
def delivered(delivery_id: str, body: dict | None = None, k: Kitchen = Depends(DELIVERY)):
    """The delivery board: a trip arrived (moved from Sent to Delivered)."""
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "DELIVERED", "delivery_id": delivery_id,
                                                       "note": (body or {}).get("note", "")})["delivery"]


@router.get("/deliveries/{delivery_id}")
def delivery(delivery_id: str, k: Kitchen = Depends(DELIVERY)):
    """One trip in full: what left, from where to where, and its run and stop (driver, ETA, who received it)."""
    stop, run = handover(delivery_id, k)
    keep = ("stop_id", "state", "eta", "receiver", "delivered_at", "driver", "note", "reason")
    return {**trip(delivery_id, k), "stop": {f: stop.get(f) for f in keep if f in stop} if stop else None,
            "run": {"run_id": run["_key"], "name": run.get("name", ""), "date": run.get("date", ""), "driver_name": run.get("driver_name", ""),
                    "vehicle": run.get("vehicle", ""), "state": run.get("state", "")} if run else None}
