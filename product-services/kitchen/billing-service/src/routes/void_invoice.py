# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""VOID_INVOICE - cancel a draft, or an issued invoice nothing was paid or credited on. Its number stays used."""
from grepx_service import RequestContext

from domain import void
from dto import Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        inv = {**void(books.invoice(ctx.text("invoice_id"))), "void_reason": ctx.text("reason")[:200], "voided_by": ctx.text("actor_name")}
        return {"invoice": books.save(Table.INVOICES.value, inv["invoice_id"], inv)}
    run(ctx, body)
