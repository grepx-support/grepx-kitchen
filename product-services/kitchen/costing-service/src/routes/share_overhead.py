# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SHARE_OVERHEAD - a cost the business pays once for several places (head-office rent, an accountant, a marketing
campaign) split over them for a month: equally, by their sales that month (the month before when none yet), or by
weights given. Each place gets its share as a line marked shared; sharing the same category again replaces it."""
from grepx_service import RequestContext

from domain import GROUPS, MONTH, SPLITS, money, split, with_share
from dto import ReasonCode, Table
from .common import business, lines_of, location, save_overhead


def sales_by_place(read, tenant: str, ids: list[str], month: str) -> dict[str, float]:
    days = read.accepted(Table.COST_DAYS.value, tenant_id=tenant)
    return {i: sum(float(d.get("sales") or 0) for d in days if d.get("location_id") == i and d.get("date", "").startswith(month)) for i in ids}


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if business(ctx.read, tenant) is None:
        return ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
    month, rule, group, category = ctx.text("month"), ctx.text("rule") or "equal", ctx.text("group") or "other", " ".join(ctx.text("category").split())[:60]
    if not MONTH.match(month):
        return ctx.reject(ReasonCode.INVALID_MONTH)
    if rule not in SPLITS or group not in GROUPS or not category:
        return ctx.reject(ReasonCode.INVALID_SPLIT)
    places = [p for p in (location(ctx.read, tenant, i) for i in ctx.get("location_ids") or []) if p]
    if not places:
        return ctx.reject(ReasonCode.NO_PLACES)
    ids = [p["_key"] for p in places]
    try:
        amount = money(ctx.get("amount"))
        if rule == "equal":
            weights = {i: 1.0 for i in ids}
        elif rule == "custom":
            weights = {i: float((ctx.get("weights") or {}).get(i) or 0) for i in ids}
        else:
            weights = sales_by_place(ctx.read, tenant, ids, month)
            if not sum(weights.values()):
                y, m = int(month[:4]), int(month[5:])
                weights = sales_by_place(ctx.read, tenant, ids, f"{y - (m == 1)}-{(m - 2) % 12 + 1:02d}")
        parts = split(amount, weights)
    except (TypeError, ValueError) as exc:
        return ctx.reject(str(exc) if str(exc) in ("INVALID_AMOUNT", "NO_PLACES") else ReasonCode.INVALID_SPLIT)
    note = ctx.text("note")[:80] or f"shared {rule}"
    rows = [save_overhead(ctx.read, ctx.emitter, tenant, p, month, with_share(lines_of(ctx.read, p["_key"], month), category, group, parts.get(p["_key"], 0), note))
            for p in places]
    ctx.accept({"shares": [{"location_id": p["_key"], "location_name": p.get("name", ""), "amount": parts.get(p["_key"], 0)} for p in places], "overheads": rows})
