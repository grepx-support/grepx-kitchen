# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""INVOICE_ORDER - an order becomes a draft invoice with the same customer, lines and rates (reference = the order
number); it is then checked and issued like any invoice. The order keeps the invoice id."""
from grepx_service import RequestContext, new_key, now_iso

from domain import invoice_from, may
from dto import QuoteState, Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        q = books.quote(ctx.text("quote_id"))
        may("invoice", q)
        invoice_id = new_key()
        invoice = books.save(Table.INVOICES.value, invoice_id, invoice_from(q, invoice_id, now_iso(), ctx.text("actor_name")))
        q = {**q, "state": QuoteState.INVOICED.value, "invoice_id": invoice_id, "invoiced_at": now_iso()}
        return {"quote": books.save(Table.QUOTES.value, q["quote_id"], q), "invoice": invoice, "invoice_id": invoice_id}
    run(ctx, body)
