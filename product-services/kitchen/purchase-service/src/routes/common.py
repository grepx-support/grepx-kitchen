# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Checks and writes shared by the purchase actions."""
from __future__ import annotations

import grepx_contracts as gc
from grepx_service import RequestContext, new_key, now_iso

from domain import message
from dto import PoState, ReasonCode, Table


class Stop(Exception):
    pass


def business(ctx: RequestContext) -> dict:
    tenant = ctx.text("tenant_id")
    if not tenant:
        raise Stop(ReasonCode.MISSING_TENANT)
    row = ctx.read.accepted_one(gc.business.BUSINESSES, tenant)
    if row is None:
        raise Stop(ReasonCode.UNKNOWN_BUSINESS)
    return row


def own(ctx: RequestContext, table: str, key: str, tenant: str, reason) -> dict:
    row = ctx.read.accepted_one(table, key) if key else None
    if row is None or row.get("tenant_id") != tenant:
        raise Stop(reason)
    return row


def order(ctx: RequestContext, tenant: str, open_only: bool = True) -> dict:
    po = own(ctx, Table.PURCHASE_ORDERS.value, ctx.text("po_id"), tenant, ReasonCode.UNKNOWN_ORDER)
    if open_only and po.get("state") != PoState.SAVED.value:
        raise Stop(ReasonCode.ALREADY_CLOSED)            # ORD-08: change or cancel only before receipt
    return po


def holding(ctx: RequestContext, tenant: str, location_id: str) -> dict:
    place = own(ctx, gc.business.LOCATIONS, location_id, tenant, ReasonCode.UNKNOWN_LOCATION)
    if not place.get("holding"):
        raise Stop(ReasonCode.NOT_HOLDING_LOCATION)      # D1 / ORD-09: supplier orders arrive at a holding place
    return place


def items(ctx: RequestContext, tenant: str, lines: list[dict]) -> dict:
    return {l["item_id"]: own(ctx, gc.item.ITEMS, l["item_id"], tenant, ReasonCode.UNKNOWN_ITEM) for l in lines}


def next_number(ctx: RequestContext, tenant: str) -> str:
    taken = [r.get("number", "") for r in ctx.read.accepted(Table.PURCHASE_ORDERS.value, tenant_id=tenant)]
    used = [int(n[3:]) for n in taken if n.startswith("PO-") and n[3:].isdigit()]
    return f"PO-{(max(used) if used else 0) + 1:04d}"


def write(ctx: RequestContext, biz: dict, po: dict, supplier: dict, place: dict, names: dict) -> dict:
    po["text"] = message(biz.get("name", ""), supplier.get("name", ""), po["number"], place.get("name", ""), po["lines"], names, po.get("note", ""))
    po["updated_at"] = now_iso()
    ctx.emitter.submit(Table.PURCHASE_ORDERS.value, po["po_id"], "ACCEPTED", po)
    return po


def new_order(ctx: RequestContext, biz: dict, supplier_id: str, location_id: str, lines: list[dict], note: str) -> dict:
    tenant = biz["_key"]
    supplier = own(ctx, gc.item.SUPPLIERS, supplier_id, tenant, ReasonCode.UNKNOWN_SUPPLIER)
    place = holding(ctx, tenant, location_id)
    names = items(ctx, tenant, lines)
    po = {"po_id": new_key()[:12], "tenant_id": tenant, "number": next_number(ctx, tenant), "supplier_id": supplier["_key"],
          "supplier_name": supplier.get("name", ""), "supplier_phone": supplier.get("phone", ""), "location_id": place["_key"],
          "lines": lines, "note": note, "state": PoState.SAVED.value, "created_at": now_iso(),
          "created_by": ctx.text("actor_id"), "created_by_name": ctx.text("actor_name")}
    return write(ctx, biz, po, supplier, place, names)


def run(ctx: RequestContext, body) -> None:
    try:
        result = body()
    except Stop as stop:
        return ctx.reject(stop.args[0])
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept({"order": result})
