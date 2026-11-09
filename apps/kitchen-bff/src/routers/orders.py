# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reorder recommendation and purchase orders (ORD-01..10)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.errors import ApiError
from grepx_bff.views import clean
from kitchen import Kitchen, allow

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


@router.get("")
def orders(state: str = "", k: Kitchen = Depends(allow("orders", "warehouse_in", module=ORD))):
    items = k.items()
    rows = [r for r in k.rows(gc.purchase.PURCHASE_ORDERS) if not state or r.get("state") == state]
    return {"orders": [po_view(k, r, items) for r in sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)]}


@router.get("/{po_id}")
def order(po_id: str, k: Kitchen = Depends(allow("orders", "warehouse_in", module=ORD))):
    po = k.one(gc.purchase.PURCHASE_ORDERS, po_id)
    if po is None:
        raise ApiError("UNKNOWN_ORDER", 404)
    return po_view(k, po, k.items())


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


@router.post("/{po_id}/cancel")
def cancel(po_id: str, k: Kitchen = Depends(buyer)):
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "CANCEL", "po_id": po_id})["order"]


@router.post("/{po_id}/receive")
def receive(po_id: str, body: dict, k: Kitchen = Depends(allow("orders", "warehouse_in", module=ORD))):
    return k.cmd(gc.purchase.REQUESTS, gc.purchase.SERVICE, {"action": "RECEIVE", "po_id": po_id, "lines": body.get("lines")})["order"]
