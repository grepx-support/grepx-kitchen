# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SUMMARY - one month for one location or the whole business: sales, ingredient cost, labour, rent, other, net profit
(COS-05, COS-06, COS-09) and the days in it."""
import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from grepx_service import RequestContext

from domain import breakdown, days_in_month, month_summary
from dto import ReasonCode, Table
from .common import business, location, overhead


def _today(biz: dict) -> date:
    try:
        return datetime.now(ZoneInfo(biz.get("timezone") or "UTC")).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def summarize(read, tenant: str, biz: dict, month: str, location_id: str = "", with_days: bool = True) -> dict:
    """One month for one location (or the whole business); raises ValueError(reason)."""
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", month):
        raise ValueError(ReasonCode.INVALID_MONTH)
    all_days = read.accepted(Table.COST_DAYS.value, tenant_id=tenant)
    if location_id:
        place = location(read, tenant, location_id)
        if place is None:
            raise ValueError(ReasonCode.UNKNOWN_LOCATION)
        places = [place]
    else:                              # whole business: every location that closed this month (kitchens included if they did)
        ids = sorted({d["location_id"] for d in all_days if d.get("date", "").startswith(month)})
        places = [p for p in (location(read, tenant, i) for i in ids) if p]
    ids = {p["_key"] for p in places}
    days = sorted((d for d in all_days if d.get("location_id") in ids and d.get("date", "").startswith(month)), key=lambda d: (d["date"], d["location_id"]))
    today = _today(biz)
    through = today.day if today.isoformat()[:7] == month else None          # the running month: overheads to date
    rows = {i: overhead(read, i, month) for i in ids}
    result = month_summary(days, rows, month, biz.get("settings") or {}, through)
    result["cost_lines"] = breakdown([r for r in rows.values() if r], min(1.0, through / days_in_month(month)) if through else 1.0)
    out = {**result, "location_id": location_id, "currency": biz.get("currency", "")}
    if with_days:
        out["days"] = [{k: v for k, v in d.items() if not k.startswith("_") and k not in ("status",)} for d in days]
    return out


def _business(ctx: RequestContext):
    tenant = ctx.text("tenant_id")
    biz = business(ctx.read, tenant) if tenant else None
    if biz is None:
        ctx.reject(ReasonCode.UNKNOWN_BUSINESS if tenant else ReasonCode.MISSING_TENANT)
    return tenant, biz


def handle(ctx: RequestContext) -> None:
    tenant, biz = _business(ctx)
    if biz is None:
        return
    try:
        ctx.accept({"summary": summarize(ctx.read, tenant, biz, ctx.text("month"), ctx.text("location_id"))})
    except ValueError as exc:
        ctx.reject(exc.args[0])


def handle_many(ctx: RequestContext) -> None:
    """SUMMARIES - several months for several locations in one go (no day rows): {location_id: {month: summary}}."""
    tenant, biz = _business(ctx)
    if biz is None:
        return
    try:
        out = {loc: {m: summarize(ctx.read, tenant, biz, m, loc, with_days=False) for m in (ctx.get("months") or [])[:24]}
               for loc in (ctx.get("location_ids") or [])[:50]}
    except ValueError as exc:
        return ctx.reject(exc.args[0])
    ctx.accept({"summaries": out})
