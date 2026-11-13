# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECORD_PAYMENT - money received against an issued invoice (part or all)."""
from grepx_service import RequestContext

from domain import pay
from dto import Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        inv = pay(books.invoice(ctx.text("invoice_id")), ctx.get("amount"), ctx.text("date") or books.today(),
                  ctx.text("method") or "bank", ctx.text("reference"), ctx.text("actor_name"))
        return {"invoice": books.save(Table.INVOICES.value, inv["invoice_id"], inv)}
    run(ctx, body)
