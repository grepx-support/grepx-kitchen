# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sales by month for a year: what was invoiced (before tax, credit notes taken off), the tax charged on it and what
customers paid. Pure; money in cents. Drafts and voided documents do not count."""
from __future__ import annotations

from dto import InvoiceState as S, Kind


def _blank() -> dict:
    return {"sales": 0, "tax": 0, "total": 0, "received": 0, "invoices": 0, "credits": 0}


def monthly(invoices: list[dict], year: int) -> list[dict]:
    months = [{"month": f"{year:04d}-{m:02d}", **_blank()} for m in range(1, 13)]
    at = {m["month"]: m for m in months}
    for inv in invoices:
        if inv.get("state") not in (S.ISSUED.value, S.PAID.value):
            continue
        row = at.get((inv.get("issued") or "")[:7])
        if row:
            sign = -1 if inv.get("kind") == Kind.CREDIT.value else 1
            row["sales"] += sign * inv.get("taxable", 0)
            row["tax"] += sign * inv.get("tax", 0)
            row["total"] += sign * inv.get("total", 0)
            row["credits" if sign < 0 else "invoices"] += 1
        for p in inv.get("payments") or []:
            if p["date"][:7] in at:
                at[p["date"][:7]]["received"] += p["amount"]
    return months
