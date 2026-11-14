# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""OVERHEADS - the monthly costs page: for the last N months (default 6) up to a month, every place's lines and group
totals with the change on the month before, the totals per month and per category, and the categories to choose from
(the standard ones and every one the business has used)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import CATEGORIES, GROUPS, MONTH, breakdown, grid
from dto import ReasonCode, Table
from .common import business


def months_to(month: str, n: int) -> list[str]:
    y, m, out = int(month[:4]), int(month[5:]), []
    for _ in range(n):
        out.append(f"{y}-{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return list(reversed(out))


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if business(ctx.read, tenant) is None:
        return ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
    month = ctx.text("month")
    if not MONTH.match(month):
        return ctx.reject(ReasonCode.INVALID_MONTH)
    months = months_to(month, max(1, min(24, int(ctx.get("months") or 6))))
    places = {p["_key"]: p.get("name", "") for p in ctx.read.accepted(gc.business.LOCATIONS, tenant_id=tenant) if p.get("active", True)}
    rows = [r for r in ctx.read.accepted(Table.OVERHEADS.value, tenant_id=tenant) if r.get("month") in months and r.get("location_id") in places]
    cells = grid(rows, places, months)
    per_month = [{"month": m, **{g: round(sum(c[g] or 0 for c in cells if c["month"] == m), 2) for g in GROUPS},
                  "total": round(sum(c["total"] or 0 for c in cells if c["month"] == m), 2)} for m in months]
    used = {l["category"]: l["group"] for r in rows for l in r.get("lines") or []}
    ctx.accept({"months": months, "groups": GROUPS, "cells": cells, "per_month": per_month,
                "categories": [{"category": c, "group": g} for c, g in {**dict(CATEGORIES), **used}.items()],
                "by_category": breakdown([r for r in rows if r.get("month") == month])})
