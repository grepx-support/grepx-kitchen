# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A forecast for one place and product: pick the method (or use the one asked for), forecast the next days, and
compare kept forecasts with what really happened. Pure."""
from __future__ import annotations

from datetime import date, timedelta

from dto import ReasonCode

from .accuracy import best, wape
from .methods import METHODS

AUTO = "auto"
MAX_DAYS = 28


def days_ahead(raw, today: date) -> list[date]:
    """The days to forecast: tomorrow onwards, 7 by default, at most 28. Refuses INVALID_DAYS."""
    try:
        n = int(raw or 7)
    except (TypeError, ValueError):
        raise ValueError(ReasonCode.INVALID_DAYS)
    if not 1 <= n <= MAX_DAYS:
        raise ValueError(ReasonCode.INVALID_DAYS)
    return [today + timedelta(days=i) for i in range(1, n + 1)]


def forecast_one(history: list[tuple[date, float]], days: list[date], method: str = AUTO) -> dict:
    if method != AUTO and method not in METHODS:
        raise ValueError(ReasonCode.UNKNOWN_METHOD)
    chosen, scores = best(history)
    chosen = chosen if method == AUTO else method
    qty = METHODS[chosen].predict(history, days) if history else [0.0] * len(days)
    return {"method": chosen, "scores": scores, "error": scores.get(chosen),
            "forecast": [{"date": d.isoformat(), "qty": round(q, 1)} for d, q in zip(days, qty)], "total": round(sum(qty), 1)}


def kept_accuracy(kept: list[dict], actual: dict[tuple[str, str], dict[str, float]], today: str) -> list[dict]:
    """For each kept day before today: forecast against what was taken (all places and products), as WAPE."""
    out = []
    for row in sorted(kept, key=lambda r: r["date"]):
        if row["date"] >= today:
            continue
        lines = row.get("lines") or []
        real = [actual.get((l["location_id"], l["item_id"]), {}).get(row["date"], 0.0) for l in lines]
        out.append({"date": row["date"], "forecast": round(sum(l["qty"] for l in lines), 1), "actual": round(sum(real), 1),
                    "error": wape(real, [l["qty"] for l in lines])})
    return out
