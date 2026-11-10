# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""REORDER_LOCATIONS - the order a business's locations are listed in: {ids: [...]} -> each location gets `sort`."""
from grepx_service import RequestContext, state_of

from domain import positions
from dto import Table
from .common import guard


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    rows = {r["_key"]: r for r in ctx.read.accepted(Table.LOCATIONS.value, tenant_id=tenant)}
    try:
        order = positions(ctx.get("ids"), set(rows))
    except ValueError as exc:
        return ctx.reject(str(exc))
    for key, n in order.items():
        if rows[key].get("sort") != n:
            ctx.emitter.submit(Table.LOCATIONS.value, key, "ACCEPTED",
                               {**state_of(rows[key]), "sort": n})
    ctx.accept({"count": len(order)})
