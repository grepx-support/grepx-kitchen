# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A valid closing (CLS-01..06): who, where, when, issues, counts, sales. Kept short on purpose (CLS-09)."""
from __future__ import annotations

from datetime import date


def _number(value, reason: str) -> float:
    try:
        number = round(float(value), 4)
    except (TypeError, ValueError):
        raise ValueError(reason)
    if number < 0 or number > 100_000_000:
        raise ValueError(reason)
    return int(number) if number.is_integer() else number


def clean_closing(raw: dict, today: date, sales_types: list[str]) -> dict:
    staff = " ".join(str(raw.get("staff_name") or "").split())
    if len(staff) < 2:
        raise ValueError("STAFF_NAME_REQUIRED")
    try:
        day = date.fromisoformat(str(raw.get("date") or today.isoformat()))
    except ValueError:
        raise ValueError("INVALID_DATE")
    if day > today or (today - day).days > 31:
        raise ValueError("INVALID_DATE")
    counts: dict[str, float] = {}
    for line in raw.get("counts") or []:
        item = str((line or {}).get("item_id") or "")
        if not item:
            raise ValueError("UNKNOWN_ITEM")
        if line.get("qty") in (None, ""):
            continue                                  # not counted: system stock stays as it is
        counts[item] = _number(line.get("qty"), "INVALID_QUANTITY")
    sales: dict[str, float] = {}
    for kind, amount in (raw.get("sales") or {}).items():
        if kind not in sales_types:
            raise ValueError("UNKNOWN_SALES_TYPE")
        if amount not in (None, ""):
            sales[kind] = _number(amount, "INVALID_AMOUNT")
    total = round(sum(sales.values()), 2)
    return {"staff_name": staff, "date": day.isoformat(), "issues": str(raw.get("issues") or "").strip()[:2000],
            "counts": [{"item_id": k, "qty": v} for k, v in counts.items()], "sales": sales,
            "total_sales": int(total) if float(total).is_integer() else total}
