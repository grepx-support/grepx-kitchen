# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reorder recommendation and purchase orders (ORD-01..10), with each order's stage, timeline and bills."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.errors import ApiError
from grepx_bff.views import clean
from kitchen import Kitchen, allow
from views import line_view, stage, timeline

router = APIRouter(prefix="/orders", tags=["orders"])
ORD = "orders"
buyer = allow("orders", module=ORD)


def po_view(k: Kitchen, po: dict, items: dict) -> dict:
    v = clean(po)
    v["lines"] = [{**l, "item_name": items.get(l["item_id"], {}).get("name", l["item_id"]), "unit": items.get(l["item_id"], {}).get("unit", "")}
                  for l in po.get("lines") or []]
    if not k.can("view_costs"):
        return v
    v["value"] = round(sum(float(l["qty"]) * float(items.get(l["item_id"], {}).get("cost") or 0) for l in po.get("lines") or []), 2)
    return v


@router.get("/recommendation")
def recommendation(location_id: str, k: Kitchen = Depends(buyer)):
    plan = k.cmd(gc.planning.REQUESTS, gc.planning.SERVICE, {"action": "REORDER", "location_id": location_id})["plan"]
    suppliers = {r["_key"]: r.get("name", "") for r in k.rows(gc.item.SUPPLIERS)}
    for line in plan["lines"]:
        line["supplier_name"] = suppliers.get(line.get("supplier_id", ""), "")
    return plan


@router.get("/suppliers")
def suppliers(k: Kitchen = Depends(buyer)):
    """The business's active suppliers, for starting an order by hand."""
    rows = [r for r in k.rows(gc.item.SUPPLIERS) if r.get("active", True)]
    return {"suppliers": sorted(({"id": r["_key"], "name": r.get("name", "")} for r in rows), key=lambda r: r["name"].lower())}


def bills_by_order(k: Kitchen) -> dict[str, list[dict]]:
    """The supplier bills of each order (payables-service), for people who may see them."""
    if not (k.can("payables") or k.can("manage_business")):
        return {}
    out: dict[str, list[dict]] = {}
    for b in k.rows(gc.payables.BILLS):
        if b.get("po_id"):
            out.setdefault(b["po_id"], []).append(clean(b))
    return out


@router.get("")
def orders(state: str = "", k: Kitchen = Depends(allow("orders", "warehouse_in", module=ORD))):
    items, bills, places = k.items(), bills_by_order(k), {r["_key"]: r.get("name", "") for r in k.rows(gc.business.LOCATIONS)}
    rows = [r for r in k.rows(gc.purchase.PURCHASE_ORDERS) if not state or r.get("state") == state]
    return {"orders": [{**po_view(k, r, items), "stage": stage(r, bills.get(r["_key"], [])), "location_name": places.get(r.get("location_id"), "")}
                       for r in sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)]}


@router.get("/{po_id}")
def order(po_id: str, k: Kitchen = Depends(allow("orders", "warehouse_in", module=ORD))):
    """One order with everything about it: lines ordered against received (with values for cost viewers), supplier
    contact, where it goes, its bills and its timeline; and the orders before and after it (for previous / next)."""
    po = k.one(gc.purchase.PURCHASE_ORDERS, po_id)
    if po is None:
        raise ApiError("UNKNOWN_ORDER", 404)
    items, bills = k.items(), bills_by_order(k).get(po_id, [])
    supplier = k.one(gc.item.SUPPLIERS, po.get("supplier_id", "")) or {}
    place = k.one(gc.business.LOCATIONS, po.get("location_id", "")) or {}
    order_ids = [r["_key"] for r in sorted(k.rows(gc.purchase.PURCHASE_ORDERS), key=lambda r: r.get("created_at", ""), reverse=True)]
    at = order_ids.index(po_id) if po_id in order_ids else -1
    cur = (k.business.get("currency") or "")
    return {**po_view(k, po, items), "stage": stage(po, bills), "location_name": place.get("name", ""),
            "supplier": {"name": supplier.get("name", po.get("supplier_name", "")), "phone": supplier.get("phone", ""),
                         "email": supplier.get("email", ""), "contact": supplier.get("contact", "")},
            "line_view": line_view(po, items, k.can("view_costs")),
            "bills": [{"bill_id": b["bill_id"], "ref": b.get("supplier_ref", ""), "state": b.get("state"), "total": b.get("total"),
                       "balance": b.get("balance"), "match": b.get("match")} for b in bills],
            "timeline": timeline(po, bills, lambda c: f"{cur} {c / 100:,.2f}".strip()),
            "prev_id": order_ids[at - 1] if at > 0 else "", "next_id": order_ids[at + 1] if 0 <= at < len(order_ids) - 1 else ""}


@router.post("")
def save(body: dict, k: Kitchen = Depends(buyer)):
    fields = {f: body[f] for f in ("supplier_id", "location_id", "note") if f in body}
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "SAVE", **fields, "lines": body.get("lines") or []})["order"]


@router.post("/{po_id}")
def change(po_id: str, body: dict, k: Kitchen = Depends(buyer)):
    fields = {f: body[f] for f in ("supplier_id", "location_id", "note") if f in body}
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "SAVE", "po_id": po_id, **fields, "lines": body.get("lines") or []})["order"]


@router.post("/{po_id}/copy")
def copy(po_id: str, k: Kitchen = Depends(buyer)):
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "COPY", "po_id": po_id})["order"]


@router.post("/{po_id}/send")
def send(po_id: str, body: dict, k: Kitchen = Depends(buyer)):
    """Send the order to the supplier (email / WhatsApp / SMS; only logged until the business connects a provider)."""
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "SEND", "po_id": po_id, "channels": body.get("channels") or []})["order"]


@router.post("/{po_id}/cancel")
def cancel(po_id: str, k: Kitchen = Depends(buyer)):
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "CANCEL", "po_id": po_id})["order"]


@router.post("/{po_id}/receive")
def receive(po_id: str, body: dict, k: Kitchen = Depends(allow("orders", "warehouse_in", module=ORD))):
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "RECEIVE", "po_id": po_id, "lines": body.get("lines")})["order"]
