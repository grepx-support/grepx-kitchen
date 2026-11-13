# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""STATEMENT (read only) - one customer's invoices, credit notes and payments with a running balance, and what is open."""
from grepx_service import RequestContext

from domain import statement
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        customer = books.customer(ctx.text("customer_id"))
        return {"customer": customer, "today": books.today(), **statement(books.invoices(), customer["customer_id"], books.today())}
    run(ctx, body)
