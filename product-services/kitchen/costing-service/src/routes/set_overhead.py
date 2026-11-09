# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_OVERHEAD - labour, rent and other costs of one location for one month (COS-02, Q10); recosts that month's days."""
import re

import grepx_contracts as gc
from grepx_service import RequestContext

from dto import ReasonCode, Table
from .common import business, compute_day, location


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(ReasonCode.MISSING_TENANT)
    if business(ctx.read, tenant) is None:
        return ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
    place = location(ctx.read, tenant, ctx.text("location_id"))
    if place is None:
        return ctx.reject(ReasonCode.UNKNOWN_LOCATION)
    month = ctx.text("month")
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", month):
        return ctx.reject(ReasonCode.INVALID_MONTH)
    row = {"tenant_id": tenant, "location_id": place["_key"], "month": month}
    for line in ("labour", "rent", "other"):
        try:
            value = float(ctx.get(line))
        except (TypeError, ValueError):
            return ctx.reject(ReasonCode.INVALID_AMOUNT, line)
        if value < 0:
            return ctx.reject(ReasonCode.INVALID_AMOUNT, line)
        row[line] = round(value, 2)
    ctx.emitter.submit(Table.OVERHEADS.value, f"{place['_key']}:{month}", "ACCEPTED", row)
    for closing in ctx.read.accepted(gc.closing.CLOSINGS, tenant_id=tenant, location_id=place["_key"]):
        if closing.get("date", "").startswith(month):
            compute_day(ctx.read, ctx.emitter, tenant, place["_key"], closing["date"])
    ctx.accept({"overhead": row})
