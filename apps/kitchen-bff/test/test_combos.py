# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Combos and breaking down through the kitchen API: a sold meal box takes its parts; a whole chicken becomes cuts."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def item(api, owner, name, **extra):
    return ok(api.post("/api/v1/setup/items", headers=owner, json={"name": name, "kind": "ingredient", "unit": "each", "cost": 1, **extra}))["item_id"]


def test_combo_sale_and_break_down(env):
    stack, api = env
    owner = open_business(api, "Combo Kitchen", "owner@combo.sg")["owner"]
    wh = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Central", "kind": "warehouse"}))["location_id"]
    rice, curry = item(api, owner, "Rice tub"), item(api, owner, "Curry tub")
    box = item(api, owner, "Meal box", kind="finished", price=12, components=[{"item_id": rice, "qty": 1}, {"item_id": curry, "qty": 2}])
    breast, wing = item(api, owner, "Breast"), item(api, owner, "Wing")
    chicken = item(api, owner, "Whole chicken", breaks_into=[{"item_id": breast, "qty": 2}, {"item_id": wing, "qty": 2}])
    assert api.post("/api/v1/setup/items", headers=owner, json={"name": "Loop", "kind": "finished", "unit": "each", "components": [{"item_id": "nope", "qty": 1}]}).status_code >= 400
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": rice, "qty": 10}, {"item_id": curry, "qty": 10}, {"item_id": chicken, "qty": 3}]}))
    cust = ok(api.post("/api/v1/sales/customers", headers=owner, json={"name": "Office"}))["customer_id"]
    inv = ok(api.post("/api/v1/sales/invoices", headers=owner, json={"customer_id": cust, "location_id": wh, "lines": [{"item_id": box, "qty": 3}]}))["invoice_id"]
    ok(api.post(f"/api/v1/sales/invoices/{inv}/issue", headers=owner, json={}))
    ok(api.post("/api/v1/stock/break-down", headers=owner, json={"location_id": wh, "lines": [{"item_id": chicken, "qty": 2}],
                                                                 "outputs": [{"item_id": breast, "qty": 4}, {"item_id": wing, "qty": 3}]}))
    stack.settle()
    level = {l["item_id"]: l["qty"] for l in ok(api.get("/api/v1/stock", headers=owner))["levels"] if l["location_id"] == wh}
    assert (level[rice], level[curry], level[chicken], level[breast], level[wing]) == (7, 4, 1, 4, 3)
    assert box not in level or level[box] == 0
