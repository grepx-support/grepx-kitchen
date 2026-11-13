# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Inventory control rules (no I/O).

Par levels   each item at each place may have a minimum (below it: alert, reorder) and a maximum (fill up to it).
Alerts       low (under the minimum), negative (the system shows less than nothing: a count is due), expiring (a lot ends
             within EXPIRY_DAYS), expired (a lot is past its date). One alert per kind, place and item per day.
Stock take   the expected quantities are frozen when it starts; variance = counted - expected, valued at the item's cost.
Valuation    on hand x current cost, and by lot (lots that carry their own cost; stock without lots at current cost).
ABC          items ranked by the value they consumed in the period: A = the first 80% of value, B = the next 15%, C = the rest.
Days of cover  on hand / average daily consumption.
Consumption  count drops, waste and use outside kitchens (the same rule as cost of goods), plus kitchen use for ingredients.
"""
from __future__ import annotations

EXPIRY_DAYS = 2
CONSUMED = ("count", "waste", "use", "sale")


def clean_par(raw: dict) -> dict:
    try:
        low = float(raw.get("min") or 0)
        high = float(raw["max"]) if raw.get("max") not in (None, "") else None
    except (TypeError, ValueError):
        raise ValueError("INVALID_LEVEL")
    if low < 0 or (high is not None and high < low):
        raise ValueError("INVALID_LEVEL")
    return {"min": round(low, 4), "max": None if high is None else round(high, 4)}


def alerts(day: str, levels: list[dict], pars: dict[tuple, dict], lots: list[dict], expiry_days: int = EXPIRY_DAYS) -> list[dict]:
    """Today's alerts: [{kind, location_id, item_id, qty, limit, expiry, lot_id}]."""
    from datetime import date
    out = []
    for lv in levels:
        key, qty = (lv["location_id"], lv["item_id"]), float(lv.get("qty") or 0)
        par = pars.get(key) or {}
        if qty < 0:
            out.append({"kind": "negative", "location_id": key[0], "item_id": key[1], "qty": qty})
        elif par.get("min") and qty < par["min"]:
            out.append({"kind": "low", "location_id": key[0], "item_id": key[1], "qty": qty, "limit": par["min"],
                        "fill_to": par.get("max") or par["min"]})
    today = date.fromisoformat(day)
    for lot in lots:
        if not lot.get("expiry") or float(lot.get("qty") or 0) <= 0:
            continue
        left = (date.fromisoformat(lot["expiry"]) - today).days
        if left < 0 or left <= expiry_days:
            out.append({"kind": "expired" if left < 0 else "expiring", "location_id": lot["location_id"], "item_id": lot["item_id"],
                        "qty": lot["qty"], "expiry": lot["expiry"], "lot_id": lot.get("lot_id", ""), "days_left": left})
    return out


def alert_key(tenant: str, day: str, a: dict) -> str:
    return f"{tenant}:{day}:{a['kind']}:{a['location_id']}:{a['item_id']}:{a.get('lot_id', '')}"


def variance(lines: list[dict], costs: dict[str, float]) -> list[dict]:
    out = []
    for l in lines:
        if l.get("counted") is None:
            continue
        diff = round(float(l["counted"]) - float(l.get("expected") or 0), 4)
        out.append({**l, "variance": diff, "value": round(diff * costs.get(l["item_id"], 0.0), 2)})
    return out


def valuation(levels: list[dict], costs: dict[str, float], lots: list[dict]) -> list[dict]:
    lot_value: dict[tuple, tuple[float, float]] = {}
    for lot in lots:
        if float(lot.get("qty") or 0) > 0 and lot.get("unit_cost") is not None:
            k = (lot["location_id"], lot["item_id"])
            q, v = lot_value.get(k, (0.0, 0.0))
            lot_value[k] = (q + lot["qty"], v + lot["qty"] * float(lot["unit_cost"]))
    out = []
    for lv in levels:
        k, qty = (lv["location_id"], lv["item_id"]), float(lv.get("qty") or 0)
        cost = costs.get(lv["item_id"], 0.0)
        in_lots, by_lots = lot_value.get(k, (0.0, 0.0))
        rest = max(0.0, qty - in_lots)
        # the lots' value, cut down in proportion when fewer are left than the lots hold (none at all: a level below zero)
        in_hand = by_lots if qty >= in_lots else (by_lots * max(qty, 0.0) / in_lots if in_lots > 0 else 0.0)
        out.append({"location_id": k[0], "item_id": k[1], "qty": qty, "unit_cost": cost, "value": round(qty * cost, 2),
                    "lot_value": round(min(by_lots, in_hand) + rest * cost, 2)})
    return out


def consumption(moves: list[dict], kitchens: set[str], finished: set[str]) -> dict[str, dict]:
    """item -> {"qty", "value"} consumed (positive numbers)."""
    used: dict[str, dict] = {}
    for m in moves:
        kind, qty = m.get("kind"), float(m.get("qty") or 0)
        if kind not in CONSUMED or qty >= 0:
            continue
        if kind == "use" and m.get("location_id") in kitchens and m.get("item_id") in finished:
            continue
        u = used.setdefault(m["item_id"], {"qty": 0.0, "value": 0.0})
        u["qty"] += -qty
        u["value"] += -float(m.get("value") or 0)
    return used


def abc(used: dict[str, dict]) -> dict[str, str]:
    total = sum(u["value"] for u in used.values()) or 1.0
    out, running = {}, 0.0
    for item, u in sorted(used.items(), key=lambda kv: -kv[1]["value"]):
        share = running / total
        out[item] = "A" if share < 0.8 else "B" if share < 0.95 else "C"
        running += u["value"]
    return out


def cover(on_hand: dict[str, float], used: dict[str, dict], days: int) -> dict[str, float | None]:
    return {item: (round(qty / (used[item]["qty"] / days), 1) if used.get(item, {}).get("qty") else None) for item, qty in on_hand.items()}


def waste_by_reason(moves: list[dict], costs: dict[str, float] | None = None) -> dict[str, float]:
    """Value thrown away, by reason. Finished goods carry no value in stock (their ingredients were costed when cooked),
    so for this report they are valued at the item's cost - what was lost, not a second cost of goods."""
    out: dict[str, float] = {}
    for m in moves:
        if m.get("kind") == "waste":
            r = m.get("waste_reason") or "other"
            value = -float(m.get("value") or 0) or abs(float(m.get("qty") or 0)) * (costs or {}).get(m.get("item_id", ""), 0.0)
            out[r] = round(out.get(r, 0.0) + value, 2)
    return out
