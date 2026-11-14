# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Usage = what was consumed: ingredients a kitchen recorded as used, plus what disappeared between counts (sold or
wasted at a store - a count lower than the system stock). Adjustments correct errors and are not usage (R3).

The window is the last N full days before today (N = 7 x target_weeks, R5 / KIT-03). A business with less history than
the window is averaged over the days it has (from its first movement), so a new business is not under-planned; with no
history at all the averages are None and people enter quantities by hand (KIT-10, ORD-10).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

CONSUMED = {"use", "count"}


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


class Usage:
    def __init__(self, movements: list[dict], today: date, weeks: int):
        self.today, self.weeks = today, max(1, min(3, int(weeks or 1)))
        start = today - timedelta(days=7 * self.weeks)
        firsts = [m["date"] for m in movements if m.get("date")]
        first = min(firsts) if firsts else None
        self.days = 0
        if first:
            self.days = max(0, min((today - date.fromisoformat(first)).days, 7 * self.weeks))
        self.by_place: dict[tuple, float] = defaultdict(float)
        self.by_item: dict[str, float] = defaultdict(float)
        for m in movements:
            if m.get("kind") not in CONSUMED or not m.get("date") or not start.isoformat() <= m["date"] < today.isoformat():
                continue
            used = -float(m.get("qty") or 0)          # a decrease is usage; a count above the books gives some back
            self.by_place[(m["location_id"], m["item_id"])] += used
            self.by_item[m["item_id"]] += used

    @property
    def has_history(self) -> bool:
        return self.days >= 1

    def daily(self, item_id: str, location_id: str | None = None) -> float | None:
        if not self.has_history:
            return None
        total = self.by_place.get((location_id, item_id), 0.0) if location_id else self.by_item.get(item_id, 0.0)
        return max(0.0, total) / self.days

    def weekly(self, item_id: str, location_id: str | None = None) -> float | None:
        d = self.daily(item_id, location_id)
        return None if d is None else d * 7
