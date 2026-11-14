# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_LOCATION - add or change a kitchen, warehouse, store or truck (BUS-02, BUS-04, INV-04, CLS-07)."""
from grepx_service import RequestContext, new_key

from domain import clean_location, holding_left
from dto import ReasonCode, Table
from .common import guard

FIELDS = ("name", "kind", "holding", "days_of_cover", "count_every_days", "active", "address")


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    location_id = ctx.text("location_id")
    current = ctx.read.accepted_one(Table.LOCATIONS.value, location_id) if location_id else None
    if location_id and (current is None or current.get("tenant_id") != tenant):
        return ctx.reject(ReasonCode.UNKNOWN_LOCATION)
    location_id = location_id or new_key()[:12]
    try:
        row = clean_location({k: ctx.get(k) for k in FIELDS if ctx.get(k) is not None}, current)
    except ValueError as exc:
        return ctx.reject(str(exc))
    others = ctx.read.accepted(Table.LOCATIONS.value, tenant_id=tenant)
    if not holding_left(others, location_id, row):
        return ctx.reject(ReasonCode.NO_HOLDING_LOCATION)
    full = {"location_id": location_id, "tenant_id": tenant, **row}
    ctx.emitter.submit(Table.LOCATIONS.value, location_id, "ACCEPTED", full)
    ctx.accept({"location": full})
