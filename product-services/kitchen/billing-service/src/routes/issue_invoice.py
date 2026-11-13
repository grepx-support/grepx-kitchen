# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ISSUE_INVOICE - a draft becomes a real invoice: next number, issue date (today, or given), due date from the customer's
terms. With send = true the customer is emailed (notification-service; only logged until a provider is set up).
When the invoice says where the goods are sent from, stock-service is asked to take its item lines out of stock there."""
import grepx_contracts as gc
from grepx_service import RequestContext, notify

from domain import due_on, next_number
from dto import InvoiceState, ReasonCode, Table
from .common import Stop, run


def send(ctx, books, inv: dict, customer: dict) -> bool:
    biz = books.business
    return bool(notify(ctx.emitter, "customer_invoice", email=customer.get("email", ""), channels=["email"],
                       ref=f"inv-{inv['invoice_id']}", tenant_id=books.tenant, auto=False,
                       values={"org": biz.get("name", ""), "customer": customer.get("name", ""), "number": inv["number"],
                               "total": f"{biz.get('currency', '')} {inv['total'] / 100:,.2f}", "due": inv["due"]}))


def take_from_stock(ctx, books, inv: dict) -> None:
    lines = [{"item_id": l["item_id"], "qty": float(l["qty"])} for l in inv["lines"] if l.get("item_id")]
    if inv.get("location_id") and lines:
        ctx.request(gc.stock.REQUESTS, f"inv-{inv['invoice_id']}",
                    {"action": gc.stock.StockAction.SELL.value, "tenant_id": books.tenant, "location_id": inv["location_id"], "lines": lines,
                     "invoice_id": inv["invoice_id"], "invoice_number": inv["number"], "note": f"Invoice {inv['number']}",
                     "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.stock.SERVICE)


def handle(ctx: RequestContext) -> None:
    def body(books):
        inv = books.invoice(ctx.text("invoice_id"))
        if inv.get("state") != InvoiceState.DRAFT.value:
            raise Stop(ReasonCode.NOT_A_DRAFT)
        customer = books.customer(inv["customer_id"])
        issued = ctx.text("issued") or books.today()
        try:
            due = due_on(issued, customer.get("terms_days", 30))
        except ValueError:
            raise Stop(ReasonCode.INVALID_DATE)
        number = next_number(inv["kind"], int(issued[:4]), [i.get("number", "") for i in books.invoices()])
        inv = {**inv, "state": InvoiceState.ISSUED.value, "number": number, "issued": issued, "due": due, "issued_by": ctx.text("actor_name")}
        if ctx.get("send") and not send(ctx, books, inv, customer):
            raise Stop(ReasonCode.NO_EMAIL)
        saved = books.save(Table.INVOICES.value, inv["invoice_id"], inv)
        take_from_stock(ctx, books, inv)
        return {"invoice": saved}
    run(ctx, body)
