# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Landed cost through the kitchen API: freight and duty on a bill spread into the items' real cost, which becomes
their cost when the bill is approved (with history)."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_landed_cost_recosts_items(env):
    stack, api = env
    owner = open_business(api, "Landed Kitchen", "owner@landed.sg")["owner"]
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Spice Imports"}))["supplier_id"]
    pepper = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Pepper", "kind": "ingredient", "unit": "kg", "cost": 10}))["item_id"]
    bill = ok(api.post("/api/v1/bills", headers=owner, json={"supplier_id": sup, "supplier_ref": "SI-9", "bill_date": "2026-11-01",
                                                             "lines": [{"item_id": pepper, "qty": 10, "unit_price": "10"}],
                                                             "landed": [{"kind": "freight", "amount": "15"}, {"kind": "duty", "amount": "5", "on_bill": False}]}))
    b = bill["bill"]
    assert (b["landed_total"], b["total"], b["lines"][0]["landed_unit"]) == (2000, 11500, "1200.00")
    ok(api.post(f"/api/v1/bills/{bill['bill_id']}/approve", headers=owner, json={"note": ""}))
    stack.settle()
    item = next(i for i in ok(api.get("/api/v1/setup", headers=owner))["items"] if i["id"] == pepper)
    assert item["cost"] == 12 and item["cost_history"][0]["source"] == "Bill SI-9"
