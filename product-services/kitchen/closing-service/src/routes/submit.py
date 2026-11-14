# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SUBMIT - save the closing and have stock-service replace system stock with the count (CLS-08, Q6).

One closing per location and day. The expected quantity next to each count is the system stock at submission (CLS-03).
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_service import RequestContext, now_iso

from domain import clean_closing
from dto import ReasonCode, Table


def _today(business: dict):
    try:
        return datetime.now(ZoneInfo(business.get("timezone") or "UTC")).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(ReasonCode.MISSING_TENANT)
    business = ctx.read.accepted_one(gc.business.BUSINESSES, tenant)
    if business is None:
        return ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
    place = ctx.read.accepted_one(gc.business.LOCATIONS, ctx.text("location_id"))
    if place is None or place.get("tenant_id") != tenant or not place.get("active", True):
        return ctx.reject(ReasonCode.UNKNOWN_LOCATION)
    types = list((business.get("settings") or {}).get("sales_types") or ["Sales", "Other sales"])
    try:
        closing = clean_closing({"staff_name": ctx.text("staff_name") or ctx.text("actor_name"), "date": ctx.text("date"),
                                 "issues": ctx.text("issues"), "counts": ctx.get("counts") or [], "sales": ctx.get("sales") or {}},
                                _today(business), types)
    except ValueError as exc:
        return ctx.reject(str(exc))
    closing_id = f"{place['_key']}:{closing['date']}"
    if ctx.read.accepted_one(Table.CLOSINGS.value, closing_id) is not None:
        return ctx.reject(ReasonCode.ALREADY_SUBMITTED)
    for line in closing["counts"]:
        item = ctx.read.accepted_one(gc.item.ITEMS, line["item_id"])
        if item is None or item.get("tenant_id") != tenant:
            return ctx.reject(ReasonCode.UNKNOWN_ITEM, line["item_id"])
        level = ctx.read.accepted_one(gc.stock.STOCK_LEVELS, f"{place['_key']}:{line['item_id']}") or {}
        line["expected"] = level.get("qty", 0)
    row = {"closing_id": closing_id, "tenant_id": tenant, "location_id": place["_key"], "location_name": place.get("name", ""),
           "staff_id": ctx.text("actor_id"), **closing, "submitted_at": now_iso()}
    ctx.emitter.submit(Table.CLOSINGS.value, closing_id, "ACCEPTED", row)
    ctx.request(gc.stock.REQUESTS, f"count-{closing_id}",
                {"action": gc.stock.StockAction.COUNT.value, "tenant_id": tenant, "location_id": place["_key"], "date": closing["date"],
                 "lines": [{"item_id": l["item_id"], "qty": l["qty"]} for l in closing["counts"]] or [],
                 "ref": closing_id, "note": "Closing count", "actor_id": ctx.text("actor_id"), "actor_name": closing["staff_name"]},
                gc.stock.SERVICE)
    ctx.accept({"closing": row})
