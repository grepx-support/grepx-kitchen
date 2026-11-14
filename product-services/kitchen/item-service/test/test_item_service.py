# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""item-service: items, suppliers and simple recipes - each business sees only its own."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_item
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "item_requests"


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "name": "HFT"})
    harness.seed("businesses", "cafe", {"business_id": "cafe", "tenant_id": "cafe", "name": "Cafe"})
    return harness


def call(h, **fields):
    return h.call(T, "item-service", fields)


def test_item_rules():
    assert clean_item({"name": " Beef  chuck ", "kind": "ingredient", "unit": "kg", "cost": "12.5"})["name"] == "Beef chuck"
    with pytest.raises(ValueError, match="INVALID_COST"):
        clean_item({"name": "Beef", "kind": "ingredient", "unit": "kg", "cost": -1})


def test_items_suppliers_recipes(h):
    s = call(h, action="SAVE_SUPPLIER", tenant_id="hft", name="Fresh Meats", phone="+61 400 000 000")
    assert s.ok and s.fields["supplier"]["phone"] == "+61400000000"
    sid = s.fields["supplier"]["supplier_id"]
    beef = call(h, action="SAVE_ITEM", tenant_id="hft", name="Beef", kind="ingredient", unit="kg", cost=12, supplier_id=sid)
    assert beef.ok
    birria = call(h, action="SAVE_ITEM", tenant_id="hft", name="Birria", kind="finished", unit="box", cost=6.5)
    bid, beef_id = birria.fields["item"]["item_id"], beef.fields["item"]["item_id"]
    assert call(h, action="SAVE_ITEM", tenant_id="hft", name="beef", kind="ingredient", unit="kg").reason == "DUPLICATE_NAME"
    r = call(h, action="SAVE_RECIPE", tenant_id="hft", item_id=bid, batch_output=10, ingredients=[{"item_id": beef_id, "qty": 4.5}])
    assert r.ok and r.fields["recipe"]["ingredients"][0]["qty"] == 4.5
    assert call(h, action="SAVE_RECIPE", tenant_id="hft", item_id=beef_id, batch_output=1).reason == "NOT_FINISHED_GOOD"
    assert call(h, action="SAVE_RECIPE", tenant_id="hft", item_id=bid, batch_output=0).reason == "INVALID_QUANTITY"
    # BUS-05: another business cannot see or use these rows
    assert call(h, action="SAVE_ITEM", tenant_id="cafe", item_id=beef_id, cost=1).reason == "UNKNOWN_ITEM"
    assert call(h, action="SAVE_ITEM", tenant_id="cafe", name="Milk", kind="ingredient", unit="l", supplier_id=sid).reason == "UNKNOWN_SUPPLIER"
    assert call(h, action="SAVE_ITEM", tenant_id="ghost", name="Milk", kind="ingredient", unit="l").reason == "UNKNOWN_BUSINESS"
    changed = call(h, action="SAVE_ITEM", tenant_id="hft", item_id=beef_id, cost=13)
    assert changed.ok and changed.fields["item"]["cost"] == 13 and changed.fields["item"]["unit"] == "kg"


def test_reorder_sets_the_listing_order_of_own_rows_only(h):
    ids = [call(h, action="SAVE_ITEM", tenant_id="hft", name=n, kind="ingredient", unit="kg").fields["item"]["item_id"] for n in ("A", "B", "C")]
    done = call(h, action="REORDER", tenant_id="hft", list="items", ids=[ids[2], ids[0]])
    assert done.ok and done.fields["count"] == 2
    rows = {r["_key"]: r for r in h.rows("items")}
    assert (rows[ids[2]]["sort"], rows[ids[0]]["sort"]) == (0, 1) and "sort" not in rows[ids[1]]
    assert rows[ids[2]]["name"] == "C" and rows[ids[2]]["unit"] == "kg"          # the rest of the row is kept
    assert call(h, action="REORDER", tenant_id="cafe", list="items", ids=[ids[0]]).reason == "INVALID_LIST"   # not theirs
    assert call(h, action="REORDER", tenant_id="hft", list="items", ids=[ids[0], ids[0]]).reason == "INVALID_LIST"
    assert call(h, action="REORDER", tenant_id="hft", list="recipes", ids=[ids[0]]).reason == "INVALID_LIST"


def test_shelf_life_barcode_and_listing_order_survive_an_edit(h):
    item = call(h, action="SAVE_ITEM", tenant_id="hft", name="Milk", kind="ingredient", unit="l", shelf_life_days=7, barcode="9300 633 1")
    iid = item.fields["item"]["item_id"]
    call(h, action="REORDER", tenant_id="hft", list="items", ids=[iid])
    call(h, action="SAVE_ITEM", tenant_id="hft", item_id=iid, cost=1.5)
    row = {r["_key"]: r for r in h.rows("items")}[iid]
    assert (row["shelf_life_days"], row["barcode"], row["sort"], row["cost"]) == (7, "93006331", 0, 1.5)
    assert call(h, action="SAVE_ITEM", tenant_id="hft", name="Bad", kind="ingredient", unit="kg", shelf_life_days=-1).reason == "INVALID_SHELF_LIFE"


def test_an_item_keeps_its_selling_price():
    from domain import clean_item
    assert clean_item({"name": "Birria tacos", "kind": "finished", "unit": "box", "cost": 21.5, "price": "38.50"})["price"] == 38.5
    assert clean_item({"name": "Beef", "kind": "ingredient", "unit": "kg"})["price"] == 0
    with pytest.raises(ValueError, match="INVALID_PRICE"):
        clean_item({"name": "Beef", "kind": "ingredient", "unit": "kg", "price": -1})


def test_recipe_card_allergens_and_veg_marks(h):
    from domain import dish_marks
    paneer = call(h, action="SAVE_ITEM", tenant_id="hft", name="Paneer", kind="ingredient", unit="kg", allergens=["Milk"], diet="veg").fields["item"]
    egg = call(h, action="SAVE_ITEM", tenant_id="hft", name="Egg", kind="ingredient", unit="each", allergens=["eggs"], diet="egg").fields["item"]
    assert paneer["allergens"] == ["milk"] and paneer["diet"] == "veg"
    assert call(h, action="SAVE_ITEM", tenant_id="hft", name="X", kind="ingredient", unit="kg", allergens=["chalk"]).reason == "INVALID_ALLERGEN"
    assert call(h, action="SAVE_ITEM", tenant_id="hft", name="Y", kind="ingredient", unit="kg", diet="meaty").reason == "INVALID_DIET"
    dish = call(h, action="SAVE_ITEM", tenant_id="hft", name="Paneer bhurji", kind="finished", unit="portion").fields["item"]["item_id"]
    lines = [{"item_id": paneer["item_id"], "qty": 2}, {"item_id": egg["item_id"], "qty": 6}]
    assert call(h, action="SAVE_RECIPE", tenant_id="hft", item_id=dish, batch_output=10, ingredients=lines).ok
    card = call(h, action="SAVE_RECIPE_CARD", tenant_id="hft", item_id=dish, steps=["Crumble paneer", " ", "Scramble eggs"], station="Curry",
                prep_min=10, cook_min=8, yield_pct=95, portion="180 g", hold_hours=3)
    assert card.ok and card.fields["recipe"]["steps"] == ["Crumble paneer", "Scramble eggs"] and card.fields["recipe"]["station"] == "curry"
    assert card.fields["recipe"]["batch_output"] == 10 and len(card.fields["recipe"]["ingredients"]) == 2      # ingredients kept
    again = call(h, action="SAVE_RECIPE", tenant_id="hft", item_id=dish, batch_output=12, ingredients=lines).fields["recipe"]
    assert again["steps"] == ["Crumble paneer", "Scramble eggs"] and again["batch_output"] == 12                 # card kept
    assert call(h, action="SAVE_RECIPE_CARD", tenant_id="hft", item_id=dish, yield_pct=0).reason == "INVALID_YIELD"
    assert call(h, action="SAVE_RECIPE_CARD", tenant_id="hft", item_id=paneer["item_id"]).reason == "NOT_FINISHED_GOOD"
    assert call(h, action="SAVE_RECIPE_CARD", tenant_id="cafe", item_id=dish).reason == "UNKNOWN_ITEM"
    items = {paneer["item_id"]: paneer, egg["item_id"]: egg}
    assert dish_marks(lines, items) == {"allergens": ["eggs", "milk"], "diet": "egg"}
    assert dish_marks(lines + [{"item_id": "unmarked"}], items)["diet"] == ""


def test_set_costs_keeps_history():
    from domain.costs import recost
    item = {"cost": 10}
    assert recost(item, "10", "x", "t") is item
    new = recost(item, "12.5", "Bill HM-1", "2026-11-14")
    assert new["cost"] == 12.5 and new["cost_history"][0] == {"cost": 12.5, "was": 10.0, "source": "Bill HM-1", "at": "2026-11-14"}
