# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_INVOICE - create or change a draft: customer, lines, tax and discount rates, notes, and optionally the location the
goods are sent from (then issuing it takes them out of stock there). Totals are worked out here."""
from grepx_service import RequestContext, new_key, now_iso

from domain import clean_lines, priced
from dto import InvoiceState, Kind, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(books):
        key = ctx.text("invoice_id")
        old = books.invoice(key) if key else {}
        if old and old.get("state") != InvoiceState.DRAFT.value:
            raise Stop(ReasonCode.NOT_A_DRAFT)
        customer = books.customer(ctx.text("customer_id"))
        place = books.location(ctx.text("location_id")) if ctx.text("location_id") else {}
        key = key or new_key()
        doc = priced({"invoice_id": key, "kind": Kind.INVOICE.value, "state": InvoiceState.DRAFT.value, "customer_id": customer["customer_id"],
                      "customer_name": customer["name"], "lines": clean_lines(ctx.get("lines"), books.items()),
                      "tax_rate": str(ctx.get("tax_rate") or 0), "discount_rate": str(ctx.get("discount_rate") or 0),
                      "notes": ctx.text("notes")[:500], "reference": ctx.text("reference")[:60],
                      "location_id": ctx.text("location_id") if place else "", "location_name": place.get("name", ""), "currency": books.business.get("currency", ""),
                      "created_at": old.get("created_at") or now_iso(), "created_by": old.get("created_by") or ctx.text("actor_name"),
                      "paid": 0, "credited": 0, "payments": []})
        return {"invoice": books.save(Table.INVOICES.value, key, doc), "invoice_id": key}
    run(ctx, body)
