# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""MARGINS (read only) - profit per product and per customer for a period (`from` / `to`, default the month so far)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import margins, period
from dto import Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        start, end = period(ctx.text("from"), ctx.text("to"), books.today())
        names = {r["_key"]: r.get("name", "") for r in books.read.accepted(Table.CUSTOMERS.value, tenant_id=books.tenant)}
        recipes = {r["_key"]: r for r in books.read.accepted(gc.item.RECIPES, tenant_id=books.tenant)}
        return margins(books.invoices(), books.items(), names, start, end, recipes)
    run(ctx, body)
