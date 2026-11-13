# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A customer's statement (every invoice, credit note and payment with a running balance) and when an overdue invoice
is due a reminder. Pure functions over invoice rows; money in cents."""
from __future__ import annotations

from datetime import date

from dto import InvoiceState as S, Kind

from .invoices import ageing, balance

REMIND_AFTER = (1, 7, 14, 30)            # days late on which an automatic reminder goes out (once each)


def statement(invoices: list[dict], customer_id: str, today: str) -> dict:
    mine = [i for i in invoices if i.get("customer_id") == customer_id and i.get("state") in (S.ISSUED.value, S.PAID.value)]
    events = []
    for inv in mine:
        credit = inv.get("kind") == Kind.CREDIT.value
        events.append({"date": inv["issued"], "what": "credit note" if credit else "invoice", "number": inv["number"],
                       "invoice_id": inv["invoice_id"], "due": "" if credit else inv.get("due", ""), "amount": -inv["total"] if credit else inv["total"]})
        events += [{"date": p["date"], "what": "payment", "number": inv["number"], "invoice_id": inv["invoice_id"], "due": "",
                    "amount": -p["amount"], "method": p.get("method", "")} for p in inv.get("payments") or []]
    events.sort(key=lambda e: (e["date"], e["what"] == "payment", e["number"]))
    running = 0
    for e in events:
        running += e["amount"]
        e["balance"] = running
    open_ones = [i for i in mine if i.get("kind") == Kind.INVOICE.value and i.get("state") == S.ISSUED.value]
    return {"lines": events, "owed": sum(balance(i) for i in open_ones), "ageing": ageing(mine, today),
            "open": [{"invoice_id": i["invoice_id"], "number": i["number"], "due": i["due"], "balance": balance(i)} for i in open_ones]}


def reminder_stage(inv: dict, today: str) -> int | None:
    """The reminder this invoice is due today (days late), if it has not had it yet."""
    if inv.get("state") != S.ISSUED.value or inv.get("kind") != Kind.INVOICE.value or not inv.get("due") or balance(inv) <= 0:
        return None
    late = (date.fromisoformat(today) - date.fromisoformat(inv["due"])).days
    reached = [d for d in REMIND_AFTER if late >= d]
    if not reached:
        return None
    done = {r.get("stage") for r in inv.get("reminders") or []}
    return None if max(reached) in done else max(reached)          # only the latest step; earlier ones missed are skipped
