# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SUMMARY - one month for one location or the whole business: sales, ingredient cost, labour, rent, other, net profit
(COS-05, COS-06, COS-09) and the days in it."""
import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from grepx_service import RequestContext

from domain import month_summary
from dto import ReasonCode, Table
from .common import business, location, overhead


def _today(biz: dict) -> date:
    try:
        return datetime.now(ZoneInfo(biz.get("timezone") or "UTC")).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    biz = business(ctx.read, tenant) if tenant else None
    if biz is None:
        return ctx.reject(ReasonCode.UNKNOWN_BUSINESS if tenant else ReasonCode.MISSING_TENANT)
    month = ctx.text("month")
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", month):
        return ctx.reject(ReasonCode.INVALID_MONTH)
    if ctx.text("location_id"):
        place = location(ctx.read, tenant, ctx.text("location_id"))
        if place is None:
            return ctx.reject(ReasonCode.UNKNOWN_LOCATION)
        places = [place]
    else:                              # whole business: every location that closed this month (kitchens included if they did)
        days_all = ctx.read.accepted(Table.COST_DAYS.value, tenant_id=tenant)
        ids = sorted({d["location_id"] for d in days_all if d.get("date", "").startswith(month)})
        places = [p for p in (location(ctx.read, tenant, i) for i in ids) if p]
    ids = {p["_key"] for p in places}
    days = sorted((d for d in ctx.read.accepted(Table.COST_DAYS.value, tenant_id=tenant)
                   if d.get("location_id") in ids and d.get("date", "").startswith(month)), key=lambda d: (d["date"], d["location_id"]))
    today = _today(biz)
    through = today.day if today.isoformat()[:7] == month else None          # the running month: overheads to date
    result = month_summary(days, {i: overhead(ctx.read, i, month) for i in ids}, month, biz.get("settings") or {}, through)
    ctx.accept({"summary": {**result, "location_id": ctx.text("location_id"), "currency": biz.get("currency", ""),
                            "days": [{k: v for k, v in d.items() if not k.startswith("_") and k not in ("status",)} for d in days]}})
