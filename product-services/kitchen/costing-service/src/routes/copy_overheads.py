# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COPY_OVERHEADS - start a month from the month before: each place's lines (shares included) copied to every place
that has nothing for the new month yet (overwrite = true replaces what is there)."""
from grepx_service import RequestContext

from domain import MONTH
from dto import ReasonCode, Table
from .common import business, lines_of, location, save_overhead


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if business(ctx.read, tenant) is None:
        return ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
    src, dst = ctx.text("from_month"), ctx.text("to_month")
    if not (MONTH.match(src) and MONTH.match(dst)) or src == dst:
        return ctx.reject(ReasonCode.INVALID_MONTH)
    copied = []
    for row in ctx.read.accepted(Table.OVERHEADS.value, tenant_id=tenant):
        place = location(ctx.read, tenant, row.get("location_id", ""))
        if row.get("month") != src or place is None or (lines_of(ctx.read, place["_key"], dst) and not ctx.get("overwrite")):
            continue
        copied.append(save_overhead(ctx.read, ctx.emitter, tenant, place, dst, lines_of(ctx.read, place["_key"], src)))
    ctx.accept({"copied": len(copied), "overheads": copied})
