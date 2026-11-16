# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The kitchen's answers to the shared purchase-service (plugins.purchasing): goods are the kitchen's items, suppliers
come from item-service, supplier orders arrive at a holding place (the warehouse), and goods received go into
stock-service with a RECEIVE."""
import grepx_contracts as gc


def _own(ctx, table: str, key: str, tenant: str):
    row = ctx.read.accepted_one(table, key) if key else None
    return row if row and row.get("tenant_id") == tenant else None


def goods(ctx, tenant, ids):
    rows = {i: _own(ctx, gc.item.ITEMS, i, tenant) for i in ids}
    return {i: r for i, r in rows.items() if r}


def supplier(ctx, tenant, supplier_id):
    return _own(ctx, gc.item.SUPPLIERS, supplier_id, tenant)


def may_receive_at(place):
    return bool(place.get("holding"))


def receive(ctx, tenant, order, lines):
    ctx.request(gc.stock.REQUESTS, f"po-{order['po_id']}" + (f"-{order['delivery_no']}" if order.get("delivery_no", 1) > 1 else ""),
                {"action": gc.stock.StockAction.RECEIVE.value, "tenant_id": tenant, "location_id": order["location_id"],
                 "lines": lines, "ref": order["po_id"], "supplier_id": order["supplier_id"], "note": f"Purchase order {order['number']}",
                 "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.stock.SERVICE)
