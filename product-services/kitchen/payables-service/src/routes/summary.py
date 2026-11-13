# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SUMMARY (read only) - every bill with what is still to pay, what is due when, and this month's payments."""
from grepx_service import RequestContext

from domain import balance, due_buckets
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        today = ap.today()
        rows = ap.bills()
        shown = [{**r, "balance": balance(r), "overdue": r["state"] in ("entered", "approved") and r["due"] < today} for r in rows]
        return {"today": today, "bills": sorted(shown, key=lambda r: (r["state"] in ("paid", "void"), r["due"])),
                "due": due_buckets(rows, today), "to_approve": sum(1 for r in rows if r["state"] == "entered"),
                "paid_month": sum(p["amount"] for r in rows for p in r.get("payments") or [] if p["date"][:7] == today[:7])}
    run(ctx, body)
