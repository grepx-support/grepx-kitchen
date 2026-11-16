# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What the kitchen's barcode labels and scanners need: each item's own barcode (the maker's, for scanning packs as they
arrive), shelf life (use-by on batch labels), allergens and veg mark; each received lot with its id (the lot label's
code), item, expiry and batch, so scanning a lot label picks its item."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_items_and_lots_carry_what_labels_need(env):
    stack, api = env
    owner = open_business(api, "Label Kitchen", "owner@labelkitchen.test")["owner"]
    wh = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Central warehouse", "kind": "warehouse"}))["location_id"]
    flour = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Flour", "kind": "ingredient", "unit": "kg", "cost": 1.2,
                                                                     "barcode": "8901030865278", "allergens": ["gluten"], "diet": "veg",
                                                                     "shelf_life_days": 180}))["item_id"]
    item = next(i for i in ok(api.get("/api/v1/stock/items", headers=owner))["items"] if i["id"] == flour)
    assert (item["barcode"], item["allergens"], item["diet"], item["shelf_life_days"]) == ("8901030865278", ["gluten"], "veg", 180)
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": flour, "qty": 25, "expiry": "2027-05-01",
                                                                                       "lot_code": "B-2211"}]}))
    stack.settle()
    lots = ok(api.get(f"/api/v1/warehouse?location_id={wh}", headers=owner))["lots"]
    lot = next(l for l in lots if l["item_id"] == flour)
    assert lot["id"] and lot["item_name"] == "Flour" and lot["expiry"] == "2027-05-01" and lot["lot_code"] == "B-2211" and lot["received"]
