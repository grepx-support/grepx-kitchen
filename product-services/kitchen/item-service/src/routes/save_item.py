# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_ITEM - add or change an item: ingredient, finished product or supply, its unit and cost (COS-01, KIT-01)."""
from grepx_service import RequestContext, new_key, now_iso

from domain import clean_item
from dto import ReasonCode, Table
from .common import guard, mine

FIELDS = ("name", "kind", "unit", "cost", "price", "supplier_id", "active", "category", "shelf_life_days", "barcode", "allergens", "diet")


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    item_id = ctx.text("item_id")
    current = mine(ctx, Table.ITEMS.value, item_id, tenant)
    if item_id and current is None:
        return ctx.reject(ReasonCode.UNKNOWN_ITEM)
    try:
        row = clean_item({k: ctx.get(k) for k in FIELDS if ctx.get(k) is not None}, current)
    except ValueError as exc:
        return ctx.reject(str(exc))
    if row["supplier_id"] and mine(ctx, Table.SUPPLIERS.value, row["supplier_id"], tenant) is None:
        return ctx.reject(ReasonCode.UNKNOWN_SUPPLIER)
    item_id = item_id or new_key()[:12]
    same = [r for r in ctx.read.accepted(Table.ITEMS.value, tenant_id=tenant)
            if r["_key"] != item_id and r.get("name", "").lower() == row["name"].lower() and r.get("active", True)]
    if same:
        return ctx.reject(ReasonCode.DUPLICATE_NAME)
    if current is None or current.get("cost") != row["cost"]:
        row["cost_changed_at"] = now_iso()
    else:
        row["cost_changed_at"] = current.get("cost_changed_at", "")
    full = {"item_id": item_id, "tenant_id": tenant, **row}
    ctx.emitter.submit(Table.ITEMS.value, item_id, "ACCEPTED", full)
    ctx.accept({"item": full})
