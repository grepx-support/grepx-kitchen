# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reads shared by the costing actions and the count reaction."""
from __future__ import annotations

import grepx_contracts as gc

from domain import cost_day
from dto import Table


def business(read, tenant: str) -> dict | None:
    return read.accepted_one(gc.business.BUSINESSES, tenant) if tenant else None


def location(read, tenant: str, key: str) -> dict | None:
    row = read.accepted_one(gc.business.LOCATIONS, key) if key else None
    return row if row and row.get("tenant_id") == tenant else None


def overhead(read, location_id: str, month: str) -> dict | None:
    return read.accepted_one(Table.OVERHEADS.value, f"{location_id}:{month}")


def compute_day(read, emitter, tenant: str, location_id: str, day: str) -> dict | None:
    """(Re)work out the cost of the count period that the closing of `day` at `location_id` ends."""
    biz, place = business(read, tenant), location(read, tenant, location_id)
    closing = read.accepted_one(gc.closing.CLOSINGS, f"{location_id}:{day}")
    if biz is None or place is None or closing is None:
        return None
    earlier = [c["date"] for c in read.accepted(gc.closing.CLOSINGS, tenant_id=tenant, location_id=location_id) if c.get("date", "") < day]
    previous = max(earlier) if earlier else None
    after = previous or day
    moves = [m for m in read.accepted(gc.stock.STOCK_MOVEMENTS, tenant_id=tenant, location_id=location_id)
             if (after < m.get("date", "") <= day) or (previous is None and m.get("date") == day)]
    row = cost_day(closing, previous, moves, place.get("kind") == gc.business.LocationKind.KITCHEN.value,
                   overhead(read, location_id, day[:7]), biz.get("settings") or {})
    row = {"tenant_id": tenant, "location_id": location_id, "location_name": place.get("name", ""), **row}
    emitter.submit(Table.COST_DAYS.value, f"{location_id}:{day}", "ACCEPTED", row)
    return row
