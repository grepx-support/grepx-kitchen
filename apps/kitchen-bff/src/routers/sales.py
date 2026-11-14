# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Customers and invoices (accounts receivable) - billing-service does the work; here: who may, and the PDF."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from grepx_bff.errors import ApiError
from grepx_bff.views import clean

from documents import InvoicePdf, brand, render
from kitchen import Kitchen, allow

router = APIRouter(prefix="/sales", tags=["sales"])
seller = allow("billing", "manage_business")
A = gc.billing.BillingAction


def ask(k: Kitchen, action: A, **fields) -> dict:
    return k.cmd(gc.billing.REQUESTS, gc.billing.SERVICE, {"action": action.value, **fields})


@router.get("")
def overview(k: Kitchen = Depends(seller)):
    out = ask(k, A.SUMMARY)
    customers = [clean(r) for r in k.rows(gc.billing.CUSTOMERS)]
    return {**{f: out[f] for f in ("today", "ageing", "owed", "overdue", "invoiced_month", "received_month")}, "invoices": out["invoices"],
            "customers": sorted(customers, key=lambda c: c.get("name", "").lower()), "billing": k.business.get("billing") or {}}


@router.post("/customers")
def save_customer(body: dict, k: Kitchen = Depends(seller)):
    return ask(k, A.SAVE_CUSTOMER, **{f: body.get(f) for f in ("customer_id", "name", "email", "phone", "address", "tax_number", "contact",
                                                                "terms_days", "active", "pricing")})


@router.post("/invoices")
def save_invoice(body: dict, k: Kitchen = Depends(seller)):
    return ask(k, A.SAVE_INVOICE, **{f: body.get(f) for f in ("invoice_id", "customer_id", "lines", "tax_rate", "discount_rate", "notes", "reference",
                                                               "location_id")})


@router.get("/invoices/{invoice_id}")
def invoice(invoice_id: str, k: Kitchen = Depends(seller)):
    row = k.one(gc.billing.INVOICES, invoice_id)
    if row is None:
        raise ApiError("UNKNOWN_INVOICE", 404)
    status = next((i for i in ask(k, A.SUMMARY)["invoices"] if i["invoice_id"] == invoice_id), {})
    return {**clean(row), "status": status.get("status", ""), "balance": status.get("balance", 0),
            "customer": clean(k.one(gc.billing.CUSTOMERS, row["customer_id"])) or {}}


@router.get("/customers/{customer_id}/statement")
def statement(customer_id: str, k: Kitchen = Depends(seller)):
    return ask(k, A.STATEMENT, customer_id=customer_id)


ACTIONS = {"remind": (A.SEND_REMINDER, ()), "issue": (A.ISSUE_INVOICE, ("issued", "send")), "pay": (A.RECORD_PAYMENT, ("amount", "date", "method", "reference")),
           "void": (A.VOID_INVOICE, ("reason",)), "credit": (A.CREDIT_NOTE, ("reason", "lines"))}


@router.post("/invoices/{invoice_id}/{verb}")
def act(invoice_id: str, verb: str, body: dict, k: Kitchen = Depends(seller)):
    if verb not in ACTIONS:
        raise ApiError("NOT_FOUND", 404)
    action, fields = ACTIONS[verb]
    return ask(k, action, invoice_id=invoice_id, **{f: body.get(f) for f in fields})


@router.get("/invoices/{invoice_id}/pdf")
def pdf(invoice_id: str, k: Kitchen = Depends(seller)):
    row = k.one(gc.billing.INVOICES, invoice_id)
    if row is None:
        raise ApiError("UNKNOWN_INVOICE", 404)
    doc = clean(row)
    data = render(InvoicePdf(doc, brand(k), clean(k.one(gc.billing.CUSTOMERS, doc["customer_id"])) or {}))
    name = (doc.get("number") or "draft").replace("/", "-")
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{name}.pdf"'})


@router.get("/price")
def price(item_id: str, qty: float = 1, customer_id: str = "", k: Kitchen = Depends(seller)):
    """What an item costs this customer for this many: their own price, a quantity break, or the list price."""
    return ask(k, A.PRICE, item_id=item_id, qty=qty, customer_id=customer_id)


@router.get("/prices")
def price_list(k: Kitchen = Depends(seller)):
    """Every item you sell: list price, quantity breaks, and customers with their own price or a standing discount."""
    return ask(k, A.PRICE_LIST)


@router.put("/prices/{item_id}/breaks")
def set_breaks(item_id: str, body: dict, k: Kitchen = Depends(seller)):
    return ask(k, A.SET_PRICE_BREAKS, item_id=item_id, breaks=body.get("breaks") or [])


@router.put("/customers/{customer_id}/pricing")
def customer_pricing(customer_id: str, body: dict, k: Kitchen = Depends(seller)):
    """Set a customer's standing discount and / or their own price for one item ({item_id, price}; price null removes it)."""
    c = clean(k.one(gc.billing.CUSTOMERS, customer_id))
    if not c:
        raise ApiError("UNKNOWN_CUSTOMER", 404)
    pricing = dict(c.get("pricing") or {"discount_pct": "0", "prices": {}})
    prices = dict(pricing.get("prices") or {})
    if body.get("item_id"):
        if body.get("price") in (None, ""):
            prices.pop(body["item_id"], None)
        else:
            prices[body["item_id"]] = body["price"]
    if body.get("discount_pct") is not None:
        pricing["discount_pct"] = body["discount_pct"]
    fields = ("name", "email", "phone", "address", "tax_number", "contact", "terms_days", "active")
    return ask(k, A.SAVE_CUSTOMER, customer_id=customer_id, **{f: c.get(f) for f in fields}, pricing={**pricing, "prices": prices})["customer"]
