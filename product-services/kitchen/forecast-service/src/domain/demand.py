# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What customers took, per place, product and day, from stock movements: the count at closing (what was sold since) and
invoiced sales. Waste is not demand. Pure."""
from __future__ import annotations

from datetime import date, timedelta

DEMAND = ("count", "sale")


def daily_demand(moves: list[dict], products: set[str]) -> dict[tuple[str, str], dict[str, float]]:
    """(location_id, item_id) -> {date: qty taken} for the products (made items) only."""
    out: dict[tuple[str, str], dict[str, float]] = {}
    for m in moves:
        qty = float(m.get("qty") or 0)
        if m.get("kind") not in DEMAND or qty >= 0 or m.get("item_id") not in products:
            continue
        day = out.setdefault((m.get("location_id", ""), m["item_id"]), {})
        day[m["date"]] = day.get(m["date"], 0.0) - qty
    return out


def series(days: dict[str, float], end: date, length: int) -> list[tuple[date, float]]:
    """The last `length` days up to `end`, from the first day anything was taken; quiet days count as 0."""
    if not days:
        return []
    first = max(date.fromisoformat(min(days)), end - timedelta(days=length - 1))
    n = (end - first).days + 1
    return [(first + timedelta(days=i), days.get((first + timedelta(days=i)).isoformat(), 0.0)) for i in range(max(n, 0))]
