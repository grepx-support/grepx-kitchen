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
