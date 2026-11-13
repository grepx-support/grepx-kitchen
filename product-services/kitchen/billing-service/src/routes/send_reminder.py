# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND_REMINDER - email the customer about an unpaid invoice now (the daily job does it on days 1, 7, 14 and 30 late
when the business turned automatic reminders on)."""
from grepx_service import RequestContext

from domain import balance
from dto import InvoiceState, ReasonCode
from reminders import remind
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(books):
        inv = books.invoice(ctx.text("invoice_id"))
        if inv.get("state") != InvoiceState.ISSUED.value or balance(inv) <= 0:
            raise Stop(ReasonCode.NOT_OPEN)
        done = remind(books, ctx.emitter, inv, books.customer(inv["customer_id"]), "manual", ctx.text("actor_name"))
        if done is None:
            raise Stop(ReasonCode.NO_EMAIL)
        return {"invoice": done}
    run(ctx, body)
