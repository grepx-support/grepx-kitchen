# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Supplier returns through the kitchen API: credited on the bill and taken out of stock."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_return_goods_credits_bill_and_stock(env):
    stack, api = env
    owner = open_business(api, "Return Kitchen", "owner@returns.sg")["owner"]
    wh = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Central", "kind": "warehouse"}))["location_id"]
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Veg Co"}))["supplier_id"]
    kale = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Kale", "kind": "ingredient", "unit": "kg", "cost": 4}))["item_id"]
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": kale, "qty": 10}]}))
    bill = ok(api.post("/api/v1/bills", headers=owner, json={"supplier_id": sup, "supplier_ref": "V-1", "bill_date": "2026-11-01",
                                                             "lines": [{"item_id": kale, "qty": 10, "unit_price": "4"}]}))
    r = ok(api.post(f"/api/v1/bills/{bill['bill_id']}/return", headers=owner, json={"lines": [{"item_id": kale, "qty": 3}], "reason": "quality", "location_id": wh}))
    assert r["bill"]["credited"] == 1200
    stack.settle()
    level = next(l for l in ok(api.get(f"/api/v1/stock?location_id={wh}", headers=owner))["levels"] if l["item_id"] == kale)
    assert level["qty"] == 7
