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


def set_costs(ctx, tenant, bill, costs):
    """An approved supplier bill's landed unit costs become the items' costs (payables-service)."""
    ctx.request(gc.item.REQUESTS, f"recost-{bill['bill_id']}",
                {"action": gc.item.ItemAction.SET_COSTS.value, "tenant_id": tenant, "costs": costs, "source": f"Bill {bill.get('supplier_ref', '')}",
                 "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.item.SERVICE)


def send_back(ctx, tenant, key, location_id, lines, bill, entry):
    """Goods returned to the supplier leave stock at that place (payables-service RETURN_GOODS)."""
    ctx.request(gc.stock.REQUESTS, f"ret-{key}",
                {"action": gc.stock.StockAction.RETURN.value, "tenant_id": tenant, "location_id": location_id,
                 "lines": [{"item_id": l["item_id"], "qty": float(l["qty"])} for l in lines], "supplier_id": bill["supplier_id"],
                 "reason": entry["reason"], "ref": bill["bill_id"], "note": f"Return to {bill.get('supplier_name', '')} ({bill.get('supplier_ref', '')})",
                 "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.stock.SERVICE)
