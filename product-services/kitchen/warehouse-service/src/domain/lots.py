# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Lots: the same item in stock can be several deliveries with different expiry dates. Stock-service keeps the totals;
lots say which delivery is where, so the oldest-expiring stock leaves first (FEFO) and nothing is forgotten until it
expires.

follow() turns one accepted stock change into lot changes:
  stock leaves a place  -> lots there are used up, first expiry first (a line may name the lot it took);
  stock arrives from another place of the business -> it brings the lots it left with (same expiry, lot code);
  stock arrives from outside (receive, production, a count or correction that found more) -> a new lot, dated with the
  line's expiry, else the item's shelf life, else no date.
"""
from __future__ import annotations

from datetime import date, timedelta

PAIRED = {"send_in": "send_out", "transfer_in": "transfer_out"}
NO_DATE = "9999-12-31"
USES_KEPT = 200
WHERE = ("ref", "note", "to_location_id", "customer_id", "customer_name", "invoice_number", "trip_id")


def use_of(request_key: str, fields: dict, change: dict, qty: float, day: str) -> dict:
    """Where part of a lot went: the request, the kind of move and who / where it went to (kept on the lot for recalls)."""
    return {"request": request_key, "kind": change.get("kind", ""), "qty": qty, "date": day, "location_id": change["location_id"],
            **{k: str(fields[k]) for k in WHERE if fields.get(k)}}


def order(lot: dict) -> tuple:
    """First expiry first; lots without an expiry last; then the oldest."""
    return (lot.get("expiry") or NO_DATE, lot.get("received") or "", lot.get("lot_id") or "")


def take(lots: list[dict], qty: float, prefer: str = "") -> tuple[list[tuple[dict, float]], float]:
    """Use `qty` from these lots (the preferred lot first, then FEFO): ([(lot, taken)], shortfall)."""
    ordered = sorted((l for l in lots if l.get("qty", 0) > 0), key=lambda l: (l.get("lot_id") != prefer, *order(l)))
    out, left = [], round(qty, 4)
    for lot in ordered:
        if left <= 0:
            break
        n = min(lot["qty"], left)
        out.append((lot, n))
        left = round(left - n, 4)
    return out, max(0.0, left)


def expiry_for(line: dict, item: dict, day: str) -> str | None:
    if line.get("expiry"):
        return str(line["expiry"])[:10]
    days = item.get("shelf_life_days")
    return (date.fromisoformat(day) + timedelta(days=int(days))).isoformat() if days else None


def follow(request_key: str, fields: dict, changes: list[dict], lots: dict[tuple, list[dict]], items: dict[str, dict], day: str) -> list[dict]:
    """The lot rows to write for one accepted stock request (changed lots and new lots). Lot ids derive from the
    request key, so following the same request twice gives the same rows."""
    lines = {str(l.get("item_id")): l for l in fields.get("lines") or [] if isinstance(l, dict)}
    touched: dict[str, dict] = {}
    carried: dict[str, list[tuple[dict, float]]] = {}
    consumed: list[str] = []                                     # lots used up here (ingredients of what this request made)
    for c in changes:                                            # what left, first expiry first
        if c["qty"] >= 0:
            continue
        here = [touched.get(l["lot_id"], l) for l in lots.get((c["location_id"], c["item_id"]), [])]
        parts, _ = take(here, -c["qty"], str(lines.get(c["item_id"], {}).get("lot_id") or ""))
        for lot, n in parts:
            uses = [use_of(request_key, fields, c, n, day), *(lot.get("uses") or [])][:USES_KEPT]
            touched[lot["lot_id"]] = {**lot, "qty": round(lot["qty"] - n, 4), "uses": uses}
            if c.get("kind") not in PAIRED.values():
                consumed.append(lot["lot_id"])
        if c.get("kind") in PAIRED.values():
            carried[c["item_id"]] = parts
    new = []
    for n, c in enumerate(ch for ch in changes if ch["qty"] > 0):
        line, base = lines.get(c["item_id"], {}), {"tenant_id": fields.get("tenant_id", ""), "location_id": c["location_id"],
                                                   "item_id": c["item_id"], "received": day, "source": request_key, "bin_id": "",
                                                   "supplier_id": str(fields.get("supplier_id") or ""), "uses": []}
        if c.get("kind") in PAIRED:
            left = c["qty"]
            for m, (lot, qty) in enumerate(carried.get(c["item_id"], [])):
                new.append({**base, "lot_id": f"{request_key}-{n}-{m}", "qty": qty, "expiry": lot.get("expiry"), "parent": lot["lot_id"],
                            "lot_code": lot.get("lot_code", ""), "unit_cost": lot.get("unit_cost"), "supplier_id": lot.get("supplier_id", "")})
                left = round(left - qty, 4)
            if left > 0:                                         # stock that had no lot record (from before lots)
                new.append({**base, "lot_id": f"{request_key}-{n}-x", "qty": left, "expiry": None, "lot_code": "", "unit_cost": None})
            continue
        new.append({**base, "lot_id": f"{request_key}-{n}", "qty": c["qty"], "expiry": expiry_for(line, items.get(c["item_id"], {}), day),
                    "lot_code": str(line.get("lot_code") or "")[:40], "bin_id": str(line.get("bin_id") or ""),
                    "unit_cost": items.get(c["item_id"], {}).get("cost"),
                    **({"made_from": sorted(set(consumed))} if c.get("kind") in ("produce", "break_down") and consumed else {})})
    return [{**l, "open": l["qty"] > 0} for l in [*touched.values(), *new]]


def allocate(lots: list[dict], qty: float) -> tuple[list[dict], float]:
    """A pick line: which lots to take (bin, expiry) and what is missing."""
    parts, short = take(lots, qty)
    return [{"lot_id": l["lot_id"], "bin_id": l.get("bin_id", ""), "expiry": l.get("expiry"), "qty": n} for l, n in parts], short


def days_left(lot: dict, today: str) -> int | None:
    return (date.fromisoformat(lot["expiry"]) - date.fromisoformat(today)).days if lot.get("expiry") else None
