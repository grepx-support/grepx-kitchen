# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The books for an accounting system: a balanced journal and trial balance, Xero / QuickBooks files."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_accounting_export(env):
    stack, api = env
    owner = open_business(api, "Books Kitchen", "owner@books.sg")["owner"]
    cust = ok(api.post("/api/v1/sales/customers", headers=owner, json={"name": "Office Co"}))["customer_id"]
    inv = ok(api.post("/api/v1/sales/invoices", headers=owner, json={"customer_id": cust, "tax_rate": 9, "lines": [
        {"description": "Lunch boxes", "qty": 10, "unit_price": "10"}, {"description": "Delivery", "qty": 1, "unit_price": "20", "charge": "delivery"}]}))["invoice_id"]
    ok(api.post(f"/api/v1/sales/invoices/{inv}/issue", headers=owner, json={}))
    ok(api.post(f"/api/v1/sales/invoices/{inv}/pay", headers=owner, json={"amount": "50"}))
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Veg Co"}))["supplier_id"]
    bill = ok(api.post("/api/v1/bills", headers=owner, json={"supplier_id": sup, "supplier_ref": "V-9", "tax_rate": 9,
                                                             "lines": [{"description": "Veg", "qty": 1, "unit_price": "100"}]}))["bill_id"]
    ok(api.post(f"/api/v1/bills/{bill}/approve", headers=owner, json={}))
    stack.settle()
    d = ok(api.get('/api/v1/data/accounting?accounts={"bank":"DBS"}', headers=owner))
    tb = {a["account"]: a["balance"] for a in d["trial"]}
    assert sum(tb.values()) == 0 and tb["DBS"] == 5000 and tb["Delivery and Other Income"] == -2000 and tb["Accounts Payable"] == -10900
    csv = api.get("/api/v1/data/accounting/file?format=xero_sales&file=csv", headers=owner)
    assert csv.status_code == 200 and b"*ContactName" in csv.content and b"Office Co" in csv.content
    assert api.get("/api/v1/data/accounting/file?format=qb_bills", headers=owner).content[:2] == b"PK"
    assert api.get("/api/v1/data/accounting/file?format=nope", headers=owner).status_code == 404
