# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Recall by lot through the kitchen API: received with a lot code, sent to a kitchen, traced with names."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_recall_by_lot_code(env):
    stack, api = env
    owner = open_business(api, "Recall Kitchen", "owner@recall.sg")["owner"]
    wh = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Central", "kind": "warehouse"}))["location_id"]
    shop = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Shop", "kind": "store"}))["location_id"]
    beef = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Beef", "kind": "ingredient", "unit": "kg", "cost": 12}))["item_id"]
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": beef, "qty": 10, "lot_code": "B-77"}]}))
    stack.settle()
    ok(api.post("/api/v1/stock/send", headers=owner, json={"from_location_id": wh, "to_location_id": shop, "lines": [{"item_id": beef, "qty": 4}]}))
    stack.settle()
    assert ok(api.get("/api/v1/warehouse/lot-codes", headers=owner))["codes"][0]["code"] == "B-77"
    r = ok(api.get("/api/v1/warehouse/recall?code=b-77", headers=owner))
    assert {(l["place"], l["qty"]) for l in r["on_hand"]} == {("Central", 6), ("Shop", 4)} and r["start"][0]["item_name"] == "Beef"
    assert api.get("/api/v1/warehouse/recall?code=nope", headers=owner).status_code >= 400
