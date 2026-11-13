# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_CUSTOMER - add or change a customer (key = customer_id; new when empty)."""
from grepx_service import RequestContext, new_key

from domain import clean_customer
from dto import Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        key = ctx.text("customer_id")
        if key:
            books.customer(key)                                   # must be this business's
        key = key or new_key()
        row = books.save(Table.CUSTOMERS.value, key, {"customer_id": key, **clean_customer(ctx.fields)})
        return {"customer": row, "customer_id": key}
    run(ctx, body)
