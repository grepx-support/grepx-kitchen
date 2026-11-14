# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Price lists through the kitchen API: quantity breaks, a customer's own price and discount, charges on an invoice."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_price_lists_fill_invoices(env):
    stack, api = env
    owner = open_business(api, "Price Kitchen", "owner@prices.sg")["owner"]
    ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Store", "kind": "warehouse"}))
    taco = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Taco box", "kind": "finished", "unit": "box", "cost": 4, "price": 10}))["item_id"]
    cust = ok(api.post("/api/v1/sales/customers", headers=owner, json={"name": "Office Co"}))["customer_id"]
    ok(api.put(f"/api/v1/sales/prices/{taco}/breaks", headers=owner, json={"breaks": [{"min_qty": 20, "price": 9}]}))
    assert ok(api.get(f"/api/v1/sales/price?item_id={taco}&qty=25&customer_id={cust}", headers=owner))["source"] == "break"
    ok(api.put(f"/api/v1/sales/customers/{cust}/pricing", headers=owner, json={"item_id": taco, "price": "8.5"}))
    ok(api.put(f"/api/v1/sales/customers/{cust}/pricing", headers=owner, json={"discount_pct": "5"}))
    got = ok(api.get(f"/api/v1/sales/price?item_id={taco}&qty=2&customer_id={cust}", headers=owner))
    assert (got["unit_price"], got["source"]) == ("8.5", "customer")
    pl = ok(api.get("/api/v1/sales/prices", headers=owner))
    assert pl["items"][0]["customers"][0]["price"] == "8.5" and pl["discounts"][0]["discount_pct"] == "5"
    inv = ok(api.post("/api/v1/sales/invoices", headers=owner, json={"customer_id": cust, "lines": [
        {"item_id": taco, "qty": 10}, {"description": "Delivery", "qty": 1, "unit_price": "15", "charge": "delivery"}]}))
    one = ok(api.get(f"/api/v1/sales/invoices/{inv['invoice_id']}", headers=owner))
    assert one["lines"][0]["unit_price"] == 850 and one["charges"] == 1500
    ok(api.put(f"/api/v1/sales/customers/{cust}/pricing", headers=owner, json={"item_id": taco, "price": None}))
    assert ok(api.get(f"/api/v1/sales/price?item_id={taco}&qty=2&customer_id={cust}", headers=owner))["source"] == "list"
