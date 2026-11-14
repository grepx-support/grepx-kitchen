# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ACCEPT_QUOTE - the customer said yes (in writing, on the phone...): the quote becomes an order with its own number
(SO-2026-0001). A sent quote past its valid-until date must be sent again first (prices may have changed)."""
from grepx_service import RequestContext, now_iso

from domain import check_open, may, numbered
from dto import QuoteState, Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        q = books.quote(ctx.text("quote_id"))
        may("accept", q)
        today = books.today()
        check_open(q, today)
        number = numbered("SO", int(today[:4]), [x.get("order_number", "") for x in books.quotes()])
        q = {**q, "state": QuoteState.ORDERED.value, "order_number": number, "ordered_on": today, "accepted_at": now_iso(),
             "accepted_by": ctx.text("accepted_by")[:80] or q.get("customer_name", ""), "customer_ref": ctx.text("customer_ref")[:60],
             "recorded_by": ctx.text("actor_name")}
        return {"quote": books.save(Table.QUOTES.value, q["quote_id"], q)}
    run(ctx, body)
