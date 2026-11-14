# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Round 3: catering quotations - quote (emailed with its PDF), order, invoice - through the kitchen API."""
import base64

from kitchen_stack import env, ok, open_business  # noqa: F401


def test_quote_order_invoice(env):
    stack, api = env
    owner = open_business(api, "Party Caterers", "owner@party.sg")["owner"]
    cust = ok(api.post("/api/v1/sales/customers", headers=owner, json={"name": "Marina Events", "email": "events@marina.sg"}))["customer_id"]
    quote = ok(api.post("/api/v1/sales/quotes", headers=owner, json={
        "customer_id": cust, "event_date": "2026-12-20", "event_time": "18:30", "venue": "Marina Hall", "guests": 80, "event_name": "Year-end party",
        "tax_rate": 9, "valid_days": 10, "lines": [{"description": "Buffet menu B", "qty": 80, "unit_price": "25"}]}))
    qid = quote["quote_id"]
    assert api.post(f"/api/v1/sales/quotes/{qid}/invoice", headers=owner, json={}).status_code == 409
    draft_pdf = api.get(f"/api/v1/sales/quotes/{qid}/pdf", headers=owner)
    assert draft_pdf.status_code == 200 and draft_pdf.content[:4] == b"%PDF"
    sent = ok(api.post(f"/api/v1/sales/quotes/{qid}/send", headers=owner, json={"send": True}))["quote"]
    assert sent["state"] == "sent" and sent["number"].startswith("Q-")
    stack.settle()
    mail = [n for n in stack.rows("notifications") if n.get("template") == "catering_quote"]
    assert mail[0]["recipient"] == "events@marina.sg" and base64.b64decode(mail[0]["attachments"][0]["data_b64"])[:4] == b"%PDF"
    assert mail[0]["attachments"][0]["name"] == f"{sent['number']}.pdf"
    order = ok(api.post(f"/api/v1/sales/quotes/{qid}/accept", headers=owner, json={"accepted_by": "Ms Tan"}))["quote"]
    assert order["state"] == "ordered" and order["order_number"].startswith("SO-")
    view = ok(api.get(f"/api/v1/sales/quotes/{qid}", headers=owner))
    assert view["status"] == "ordered" and view["per_guest"] == 2725 and view["customer"]["name"] == "Marina Events"
    pipe = ok(api.get("/api/v1/sales/quotes", headers=owner))
    assert pipe["stages"]["ordered"]["count"] == 1 and pipe["win_rate"] == 100 and pipe["upcoming"][0]["quote_id"] == qid
    made = ok(api.post(f"/api/v1/sales/quotes/{qid}/invoice", headers=owner, json={}))
    inv = ok(api.get(f"/api/v1/sales/invoices/{made['invoice_id']}", headers=owner))
    assert inv["state"] == "draft" and inv["total"] == 218000 and inv["reference"] == order["order_number"]
    assert ok(api.get(f"/api/v1/sales/quotes/{qid}", headers=owner))["invoice_id"] == made["invoice_id"]
    other = open_business(api, "Elsewhere", "owner@elsewhere.sg")["owner"]
    assert api.get(f"/api/v1/sales/quotes/{qid}", headers=other).status_code == 404
