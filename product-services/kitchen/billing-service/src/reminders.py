# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sending a payment reminder for one invoice (by hand, or from the daily job) and remembering it on the invoice."""
from __future__ import annotations

from grepx_service import notify, now_iso

from dto import Table


def remind(books, emitter, inv: dict, customer: dict, stage, by: str) -> dict | None:
    """Email the customer about an unpaid invoice; None when they have no email."""
    biz = books.business
    late = stage if isinstance(stage, int) else 0
    sent = notify(emitter, "payment_reminder", email=customer.get("email", ""), channels=["email"],
                  ref=f"remind-{inv['invoice_id']}-{stage}", tenant_id=books.tenant, auto=isinstance(stage, int),
                  values={"org": biz.get("name", ""), "customer": customer.get("name", ""), "number": inv["number"], "due": inv["due"],
                          "owed": f"{biz.get('currency', '')} {(inv['total'] - inv.get('paid', 0) - inv.get('credited', 0)) / 100:,.2f}",
                          "late": f"{late} days" if late else "now", "how": (biz.get("billing") or {}).get("payment_note", "")})
    if not sent:
        return None
    inv = {**inv, "reminders": [*(inv.get("reminders") or []), {"stage": stage, "at": now_iso(), "by": by}]}
    emitter.submit(Table.INVOICES.value, inv["invoice_id"], "ACCEPTED", inv)
    return inv
