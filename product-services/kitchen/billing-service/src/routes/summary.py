# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SUMMARY (read only) - every invoice with the state a reader sees (open, part paid, overdue ...), what customers owe
by age, and this month's figures. Nothing is written."""
from grepx_service import RequestContext

from domain import ageing, balance, status
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        today = books.today()
        rows = books.invoices()
        shown = [{**r, "status": status(r, today), "balance": balance(r)} for r in rows]
        live = [r for r in shown if r["kind"] == "invoice" and r["state"] == "issued"]
        month = today[:7]
        return {"today": today, "invoices": sorted(shown, key=lambda r: (r.get("issued") or "9999", r.get("number") or ""), reverse=True),
                "ageing": ageing(rows, today), "owed": sum(r["balance"] for r in live),
                "overdue": sum(r["balance"] for r in live if r["status"] == "overdue"),
                "invoiced_month": sum(r["total"] for r in shown if r["kind"] == "invoice" and r["state"] != "void" and (r.get("issued") or "")[:7] == month),
                "received_month": sum(p["amount"] for r in shown for p in r.get("payments") or [] if p["date"][:7] == month)}
    run(ctx, body)
