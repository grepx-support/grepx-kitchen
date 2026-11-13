# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_BILL - enter (or correct, while not approved) a supplier's invoice: their number, date, due date (default: 30
days), lines, tax; optionally its purchase order, which it is matched against (ordered / received / billed, and price)."""
from grepx_money import document_lines, priced
from grepx_service import RequestContext, new_key, now_iso

from domain import check_dates, due_from, is_duplicate, match
from dto import BillState, ReasonCode
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        key = ctx.text("bill_id")
        old = ap.bill(key) if key else {}
        if old and old.get("state") != BillState.ENTERED.value:
            raise Stop(ReasonCode.NOT_ENTERED)
        supplier = ap.supplier(ctx.text("supplier_id"))
        ref = ctx.text("supplier_ref").strip()[:40]
        if not ref:
            raise Stop(ReasonCode.SUPPLIER_REF_REQUIRED)
        key = key or new_key()
        if is_duplicate(ctx.text("supplier_id"), ref, ap.bills(), key):
            raise Stop(ReasonCode.DUPLICATE_BILL)
        po = ap.order(ctx.text("po_id")) if ctx.text("po_id") else None
        if po and po.get("supplier_id") != ctx.text("supplier_id"):
            raise Stop(ReasonCode.ORDER_OF_ANOTHER_SUPPLIER)
        bill_date = ctx.text("bill_date") or ap.today()
        check_dates(bill_date)
        due = ctx.text("due") or due_from(bill_date, 30)
        check_dates(due)
        items = ap.items()
        lines = document_lines(ctx.get("lines"), items)
        state, issues = match(lines, po, ap.costs(items))
        bill = priced({"bill_id": key, "state": BillState.ENTERED.value, "supplier_id": ctx.text("supplier_id"), "supplier_name": supplier.get("name", ""),
                       "supplier_ref": ref, "bill_date": bill_date, "due": due, "po_id": (po or {}).get("po_id", ""), "po_number": (po or {}).get("number", ""),
                       "lines": lines, "tax_rate": str(ctx.get("tax_rate") or 0), "discount_rate": "0", "match": state, "issues": issues,
                       "notes": ctx.text("notes")[:500], "currency": ap.business.get("currency", ""), "paid": 0, "payments": [],
                       "entered_at": old.get("entered_at") or now_iso(), "entered_by": old.get("entered_by") or ctx.text("actor_name")})
        return {"bill": ap.save(key, bill), "bill_id": key}
    run(ctx, body)
