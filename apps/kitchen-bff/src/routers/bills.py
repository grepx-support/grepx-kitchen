# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Supplier bills (accounts payable) - payables-service matches and keeps them; here: who may, and the order to start from."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from grepx_bff.errors import ApiError
from grepx_bff.views import clean

from documents import BillPdf, brand, render
from kitchen import Kitchen, allow

router = APIRouter(prefix="/bills", tags=["bills"])
payer = allow("payables", "manage_business")
A = gc.payables.PayablesAction


def ask(k: Kitchen, action: A, **fields) -> dict:
    return k.cmd(gc.payables.REQUESTS, gc.payables.SERVICE, {"action": action.value, **fields})


@router.get("")
def overview(k: Kitchen = Depends(payer)):
    out = ask(k, A.SUMMARY)
    received = [clean(po) for po in k.rows(gc.purchase.PURCHASE_ORDERS) if po.get("state") == "received"]
    billed = {b.get("po_id") for b in out["bills"] if b.get("state") != "void"}
    return {"today": out["today"], "bills": out["bills"], "due": out["due"], "to_approve": out["to_approve"], "paid_month": out["paid_month"],
            "to_bill": [{"po_id": p["po_id"], "number": p.get("number", ""), "supplier_id": p["supplier_id"], "received_at": p.get("received_at", "")}
                        for p in sorted(received, key=lambda p: p.get("received_at", ""), reverse=True) if p["po_id"] not in billed][:20],
            "suppliers": sorted(({"id": r["_key"], "name": r.get("name", "")} for r in k.rows(gc.item.SUPPLIERS)), key=lambda s: s["name"].lower())}


@router.get("/from-order/{po_id}")
def from_order(po_id: str, k: Kitchen = Depends(payer)):
    """A new bill's lines, filled from what was received on the order at each item's current cost."""
    po = k.one(gc.purchase.PURCHASE_ORDERS, po_id)
    if po is None:
        raise ApiError("UNKNOWN_ORDER", 404)
    items = k.items()
    got = po.get("received") or po.get("lines") or []
    return {"po_id": po_id, "number": po.get("number", ""), "supplier_id": po["supplier_id"],
            "lines": [{"item_id": l["item_id"], "description": items.get(l["item_id"], {}).get("name", ""), "unit": items.get(l["item_id"], {}).get("unit", ""),
                       "qty": l["qty"], "unit_price": items.get(l["item_id"], {}).get("cost") or 0} for l in got]}


@router.post("")
def save(body: dict, k: Kitchen = Depends(payer)):
    return ask(k, A.SAVE_BILL, **{f: body.get(f) for f in ("bill_id", "supplier_id", "supplier_ref", "bill_date", "due", "po_id", "lines", "tax_rate", "notes", "landed", "recost")})


@router.get("/{bill_id}")
def bill(bill_id: str, k: Kitchen = Depends(payer)):
    row = k.one(gc.payables.BILLS, bill_id)
    if row is None:
        raise ApiError("UNKNOWN_BILL", 404)
    out = clean(row)
    items = k.items()
    out["issues"] = [{**i, "item_name": items.get(i["item_id"], {}).get("name", i["item_id"])} for i in out.get("issues") or []]
    return out


ACTIONS = {"approve": (A.APPROVE_BILL, ("note",)), "pay": (A.RECORD_PAYMENT, ("amount", "date", "method", "reference")), "void": (A.VOID_BILL, ("reason",)),
           "return": (A.RETURN_GOODS, ("lines", "reason", "note", "location_id", "date"))}


@router.post("/{bill_id}/{verb}")
def act(bill_id: str, verb: str, body: dict, k: Kitchen = Depends(payer)):
    if verb not in ACTIONS:
        raise ApiError("NOT_FOUND", 404)
    action, fields = ACTIONS[verb]
    return ask(k, action, bill_id=bill_id, **{f: body.get(f) for f in fields})


@router.get("/{bill_id}/pdf")
def pdf(bill_id: str, k: Kitchen = Depends(payer)):
    row = k.one(gc.payables.BILLS, bill_id)
    if row is None:
        raise ApiError("UNKNOWN_BILL", 404)
    doc = clean(row)
    return Response(render(BillPdf(doc, brand(k), clean(k.one(gc.item.SUPPLIERS, doc["supplier_id"])) or {})), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="bill-{doc.get("supplier_ref", "")}.pdf"'})
