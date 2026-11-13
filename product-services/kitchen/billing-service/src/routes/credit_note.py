# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CREDIT_NOTE - correct an issued invoice: a credit note (CN- number, issued now) with the lines given - or, when nothing
was paid or credited yet, a copy of all its lines (a full reversal). What the customer owes on the invoice goes down by
its total, and never below zero."""
from grepx_service import RequestContext, new_key

from domain import balance, clean_lines, credit_against, next_number, priced
from dto import InvoiceState, Kind, ReasonCode, Table
from .common import Stop, run


def reversal(inv: dict) -> list[dict]:
    if balance(inv) != inv.get("total"):
        raise Stop(ReasonCode.NO_LINES)                            # part paid: say which lines are credited
    return [{**l, "unit_price": l["unit_price"] / 100} for l in inv["lines"]]


def handle(ctx: RequestContext) -> None:
    def body(books):
        inv = books.invoice(ctx.text("invoice_id"))
        lines = ctx.get("lines") or reversal(inv)
        key, today = new_key(), books.today()
        note = priced({"invoice_id": key, "kind": Kind.CREDIT.value, "state": InvoiceState.ISSUED.value, "customer_id": inv["customer_id"],
                       "customer_name": inv["customer_name"], "lines": clean_lines(lines, books.items()), "tax_rate": inv.get("tax_rate", "0"),
                       "discount_rate": "0" if ctx.get("lines") else inv.get("discount_rate", "0"), "corrects": inv["invoice_id"], "corrects_number": inv.get("number", ""),
                       "notes": ctx.text("reason")[:500], "currency": inv.get("currency", ""), "issued": today, "due": today,
                       "paid": 0, "credited": 0, "payments": [], "issued_by": ctx.text("actor_name")})
        note["number"] = next_number(Kind.CREDIT.value, int(today[:4]), [i.get("number", "") for i in books.invoices()])
        fixed = credit_against(inv, note["total"])
        note["state"] = InvoiceState.PAID.value                    # a credit note is settled by the invoice it corrects
        books.save(Table.INVOICES.value, inv["invoice_id"], {**fixed, "credit_notes": [*(inv.get("credit_notes") or []), key]})
        return {"credit_note": books.save(Table.INVOICES.value, key, note), "invoice_id": inv["invoice_id"]}
    run(ctx, body)
