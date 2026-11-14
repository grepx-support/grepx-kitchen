# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REORDER - the order items or suppliers are listed in: {list: items|suppliers, ids: [...]} -> each row gets `sort`."""
from grepx_service import RequestContext, state_of

from domain import positions
from dto import ReasonCode, Table
from .common import guard

LISTS = {"items": Table.ITEMS.value, "suppliers": Table.SUPPLIERS.value}


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    table = LISTS.get(ctx.text("list"))
    if table is None:
        return ctx.reject(ReasonCode.INVALID_LIST)
    rows = {r["_key"]: r for r in ctx.read.accepted(table, tenant_id=tenant)}
    try:
        order = positions(ctx.get("ids"), set(rows))
    except ValueError as exc:
        return ctx.reject(str(exc))
    for key, n in order.items():
        if rows[key].get("sort") != n:
            ctx.emitter.submit(table, key, "ACCEPTED", {**state_of(rows[key]), "sort": n})
    ctx.accept({"list": ctx.text("list"), "count": len(order)})
