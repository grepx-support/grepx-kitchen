# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COGS, costing average and the monthly summary.

R7  COGS % = cost of ingredients used in the count period / sales in the same period. "Used" = what the count showed was
    consumed (system stock - counted, valued at the item's cost when it moved) plus ingredients recorded as used at a
    location that is not a kitchen. A kitchen's recorded use turns ingredients into finished goods, whose cost is counted
    where they are consumed - counting both would count the same food twice. Waste (thrown away, with a reason) is used
    stock at any location: it never reaches a sale, so it is always part of the cost.
R8 / Q9  costing average % = (ingredient cost + labour + rent + other) / sales.
Q10 labour, rent and other are monthly amounts per location, spread equally over the days of the month.
COS-06 the monthly summary never shows a profit while a cost line is missing (QR-04: the old system did).
R9 / COS-07 a period whose COGS is outside the business's range is flagged.
"""
from __future__ import annotations

import calendar
from datetime import date

OVERHEADS = ("labour", "rent", "other")


def days_in_month(month: str) -> int:
    y, m = (int(p) for p in month.split("-"))
    return calendar.monthrange(y, m)[1]


def overhead_share(overhead: dict | None, month: str, days: int) -> dict:
    """Each overhead line for `days` days of `month`; a missing line stays None."""
    out = {}
    for line in OVERHEADS:
        value = (overhead or {}).get(line)
        out[line] = None if value is None else round(float(value) / days_in_month(month) * days, 2)
    return out


def _pct(part: float, sales: float):
    return round(part / sales * 100, 1) if sales else None


def cost_day(closing: dict, previous_date: str | None, moves: list[dict], is_kitchen: bool, overhead: dict | None,
             settings: dict) -> dict:
    day = date.fromisoformat(closing["date"])
    start = date.fromisoformat(previous_date) if previous_date else day
    period_days = max(1, (day - start).days)
    used, zero_cost = 0.0, set()
    for m in moves:
        if m.get("kind") in ("count", "waste", "sale") or (m.get("kind") == "use" and not is_kitchen):
            used -= float(m.get("value") or 0)
            if not float(m.get("unit_cost") or 0) and float(m.get("qty") or 0):
                zero_cost.add(m.get("item_id"))
    sales = float(closing.get("total_sales") or 0)
    share = overhead_share(overhead, closing["date"][:7], period_days)
    missing = [k for k, v in share.items() if v is None] + (["item cost"] if zero_cost else [])
    cogs = _pct(used, sales)
    lo, hi = float(settings.get("cogs_min", 0)), float(settings.get("cogs_max", 100))
    total = used + sum(v for v in share.values() if v is not None)
    return {"date": closing["date"], "period_start": start.isoformat(), "period_days": period_days, "sales": round(sales, 2),
            "ingredient_cost": round(used, 2), **share, "cogs_pct": cogs,
            "costing_pct": None if any(v is None for v in share.values()) else _pct(total, sales),
            "out_of_range": cogs is not None and not lo <= cogs <= hi, "missing": missing, "items_without_cost": sorted(zero_cost)}


def month_summary(days: list[dict], overheads: dict[str, dict | None], month: str, settings: dict, through: int | None = None) -> dict:
    """COS-05/06/09: one month for the locations whose overheads are given (location_id -> overhead row or None).

    through: the month is running - labour, rent and other count for its first `through` days only (Q10: a monthly
    amount spread equally over the days), so the 10th of the month does not set ten days of sales against a whole month
    of rent."""
    share = 1.0 if not through else min(1.0, through / days_in_month(month))
    sales = round(sum(float(d.get("sales") or 0) for d in days), 2)
    ingredient = round(sum(float(d.get("ingredient_cost") or 0) for d in days), 2)
    lines, missing = {}, []
    for line in OVERHEADS:
        values = [(o or {}).get(line) for o in overheads.values()]
        lines[line] = None if any(v is None for v in values) else round(sum(float(v) for v in values) * share, 2)
        if lines[line] is None:
            missing.append(line)
    if any(d.get("items_without_cost") for d in days):
        missing.append("item cost")
    if not days:
        missing.append("closing days")
    complete = not missing
    cogs = _pct(ingredient, sales)
    lo, hi = float(settings.get("cogs_min", 0)), float(settings.get("cogs_max", 100))
    costs = ingredient + sum(v for v in lines.values() if v is not None)
    return {"month": month, "sales": sales, "ingredient_cost": ingredient, **lines,
            "net_profit": round(sales - costs, 2) if complete else None, "cogs_pct": cogs,
            "costing_pct": _pct(costs, sales) if complete else None, "missing": missing, "complete": complete,
            "days_out_of_range": sum(1 for d in days if d.get("out_of_range")), "closings": len(days),
            "cogs_range": [lo, hi], "overheads_days": through or days_in_month(month)}
