# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CANCEL_QUOTE - the business withdraws a quote, or cancels an order that was not invoiced yet (reason kept)."""
from grepx_service import RequestContext, now_iso

from domain import may
from dto import QuoteState, Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        q = books.quote(ctx.text("quote_id"))
        may("cancel", q)
        q = {**q, "state": QuoteState.CANCELLED.value, "closed_at": now_iso(), "close_reason": ctx.text("reason")[:200], "closed_by": ctx.text("actor_name")}
        return {"quote": books.save(Table.QUOTES.value, q["quote_id"], q)}
    run(ctx, body)
