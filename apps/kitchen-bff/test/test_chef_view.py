# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from views.chef import book


def test_cards_carry_cost_per_portion_margin_and_marks():
    items = {"p": {"_key": "p", "name": "Paneer", "kind": "ingredient", "unit": "kg", "cost": 400, "allergens": ["milk"], "diet": "veg"},
             "o": {"_key": "o", "name": "Onion", "kind": "ingredient", "unit": "kg", "cost": 40, "diet": "vegan"},
             "d": {"_key": "d", "name": "Paneer tikka", "kind": "finished", "unit": "portion", "price": 300},
             "x": {"_key": "x", "name": "Aloo", "kind": "finished", "unit": "portion"}}
    recipes = {"d": {"batch_output": 10, "yield_pct": 80, "ingredients": [{"item_id": "p", "qty": 2}, {"item_id": "o", "qty": 1}],
                     "steps": ["Marinate"], "station": "tandoor"}}
    tikka, aloo = book(items, recipes)[1], book(items, recipes)[0]
    assert tikka["unit_cost"] == 105.0 and tikka["margin_pct"] == 65.0          # (800 + 40) / (10 x 80%)
    assert tikka["allergens"] == ["milk"] and tikka["diet"] == "veg" and tikka["has_card"] and tikka["station"] == "tandoor"
    assert aloo["unit_cost"] is None and aloo["diet"] == "" and not aloo["has_card"]
