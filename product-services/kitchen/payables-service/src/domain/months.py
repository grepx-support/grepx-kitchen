# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Purchases by month for a year: supplier bills (before tax) by bill date, the tax paid on them and what was paid out.
Pure; money in cents. Voided bills do not count."""
from __future__ import annotations

from dto import BillState


def monthly(bills: list[dict], year: int) -> list[dict]:
    months = [{"month": f"{year:04d}-{m:02d}", "purchases": 0, "tax": 0, "total": 0, "paid": 0, "bills": 0} for m in range(1, 13)]
    at = {m["month"]: m for m in months}
    for bill in bills:
        if bill.get("state") == BillState.VOID.value:
            continue
        row = at.get((bill.get("bill_date") or "")[:7])
        if row:
            row["purchases"] += bill.get("taxable", 0)
            row["tax"] += bill.get("tax", 0)
            row["total"] += bill.get("total", 0)
            row["bills"] += 1
        for p in bill.get("payments") or []:
            if p["date"][:7] in at:
                at[p["date"][:7]]["paid"] += p["amount"]
    return months
