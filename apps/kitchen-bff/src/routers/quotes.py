# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Catering quotations: quote -> order -> invoice. billing-service decides every move; here: who may, the PDF, and the
PDF attached when a quote is emailed."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.errors import ApiError
from grepx_bff.views import clean

from documents import PdfFile, QuotePdf, brand
from kitchen import Kitchen
from .sales import A, ask, seller

router = APIRouter(prefix="/sales/quotes", tags=["quotes"])
FIELDS = ("quote_id", "customer_id", "lines", "tax_rate", "discount_rate", "notes", "valid_days", "event_date", "event_time", "venue", "guests", "event_name")
MOVES = {"accept": (A.ACCEPT_QUOTE, ("accepted_by", "customer_ref")), "decline": (A.DECLINE_QUOTE, ("reason",)),
         "cancel": (A.CANCEL_QUOTE, ("reason",)), "invoice": (A.INVOICE_ORDER, ())}


def quote_row(quote_id: str, k: Kitchen) -> dict:
    row = k.one(gc.billing.QUOTES, quote_id)
    if row is None:
        raise ApiError("UNKNOWN_QUOTE", 404)
    return clean(row)


def quote_file(quote_id: str, k: Kitchen) -> PdfFile:
    q = quote_row(quote_id, k)
    customer = clean(k.one(gc.billing.CUSTOMERS, q["customer_id"])) or {}
    name = q.get("order_number") if q.get("state") in ("ordered", "invoiced") else q.get("number") or "quotation-draft"
    return PdfFile(QuotePdf(q, brand(k), customer).build(), name)


@router.get("")
def pipeline(k: Kitchen = Depends(seller)):
    return ask(k, A.QUOTES)


@router.post("")
def save(body: dict, k: Kitchen = Depends(seller)):
    return ask(k, A.SAVE_QUOTE, **{f: body.get(f) for f in FIELDS})


@router.get("/{quote_id}")
def one(quote_id: str, k: Kitchen = Depends(seller)):
    q = quote_row(quote_id, k)
    view = next((x for x in ask(k, A.QUOTES)["quotes"] if x["quote_id"] == quote_id), {})
    return {**q, "status": view.get("status", q.get("state")), "per_guest": view.get("per_guest", 0),
            "customer": clean(k.one(gc.billing.CUSTOMERS, q["customer_id"])) or {}}


@router.get("/{quote_id}/pdf")
def pdf(quote_id: str, k: Kitchen = Depends(seller)):
    return quote_file(quote_id, k).response()


@router.post("/{quote_id}/send")
def send(quote_id: str, body: dict, k: Kitchen = Depends(seller)):
    """Number it and mark it sent; with send = true email it to the customer with the PDF (showing its number) attached."""
    if not body.get("send"):
        return ask(k, A.SEND_QUOTE, quote_id=quote_id)
    ask(k, A.SEND_QUOTE, quote_id=quote_id, number_only=True)
    return ask(k, A.SEND_QUOTE, quote_id=quote_id, send=True, attachments=[quote_file(quote_id, k).attachment(k.gw.storage)])


@router.post("/{quote_id}/{verb}")
def move(quote_id: str, verb: str, body: dict | None = None, k: Kitchen = Depends(seller)):
    if verb not in MOVES:
        raise ApiError("NOT_FOUND", 404)
    action, fields = MOVES[verb]
    return ask(k, action, quote_id=quote_id, **{f: (body or {}).get(f) for f in fields})
