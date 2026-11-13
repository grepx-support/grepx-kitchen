# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SELL - goods on a customer invoice leave stock at the location they are sent from (asked by billing-service when the
invoice is issued). Counts as used in that location's cost of goods; the invoice is kept on each movement."""
from grepx_service import RequestContext

from dto import MovementKind
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(book):
        place, lines = book.location(), book.lines()
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.SALE.value, "delta": -l["qty"]}
                            for l in lines], items, {"invoice_id": ctx.text("invoice_id"), "invoice_number": ctx.text("invoice_number")})
    run(ctx, body)
