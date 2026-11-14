# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_OVERHEAD - one place's costs for one month (COS-02, Q10) as lines - category, group (staff / premises / running
costs), amount, note - or, as before, just labour, rent and other. The place's shares of costs paid for several places
(SHARE_OVERHEAD) are kept. Recosts that month's days."""
from grepx_service import RequestContext

from domain import MONTH, clean_lines
from dto import ReasonCode
from .common import business, lines_of, location, save_overhead

LEGACY = {"labour": "Salaries and wages", "rent": "Rent", "other": "Other"}


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
    if not MONTH.match(month):
        return ctx.reject(ReasonCode.INVALID_MONTH)
    raw = ctx.get("lines")
    if raw is None:                                       # the old form: three amounts
        raw = [{"category": LEGACY[g], "group": g, "amount": ctx.get(g), "keep": True} for g in LEGACY]
    try:
        mine = [l for l in clean_lines(raw) if not l.get("shared")]
    except ValueError as exc:
        return ctx.reject(str(exc))
    shared = [l for l in lines_of(ctx.read, place["_key"], month) if l.get("shared")]
    ctx.accept({"overhead": save_overhead(ctx.read, ctx.emitter, tenant, place, month, mine + shared)})
