# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""planning-service: targets and recommendations come from usage; people can always type their own numbers."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import Usage, production_target, reorder, warehouse_out
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "planning_requests"
TODAY = date.today()


def day(n):
    return (TODAY - timedelta(days=n)).isoformat()


def test_usage_counts_use_and_count_drops_not_adjustments():
    moves = [{"date": day(10), "kind": "use", "qty": -14, "location_id": "k", "item_id": "beef"},
             {"date": day(3), "kind": "count", "qty": -7, "location_id": "s", "item_id": "birria"},
             {"date": day(2), "kind": "count", "qty": 1, "location_id": "s", "item_id": "birria"},
             {"date": day(2), "kind": "adjust", "qty": -50, "location_id": "s", "item_id": "birria"},
             {"date": day(1), "kind": "receive", "qty": 99, "location_id": "w", "item_id": "beef"},
             {"date": day(0), "kind": "use", "qty": -99, "location_id": "k", "item_id": "beef"}]       # today: not a full day yet
    u = Usage(moves, TODAY, 2)
    assert u.days == 10 and u.weekly("beef") == pytest.approx(9.8) and u.daily("birria", "s") == pytest.approx(0.6)
    assert Usage([], TODAY, 2).weekly("beef") is None


def test_targets_batches_ingredients_and_manual_override():
    u = Usage([{"date": day(7), "kind": "count", "qty": -70, "location_id": "s", "item_id": "birria"}], TODAY, 1)
    r = production_target([{"_key": "birria", "name": "Birria"}, {"_key": "tulang", "name": "Tulang"}],
                          {"birria": {"batch_output": 17, "ingredients": [{"item_id": "beef", "qty": 5}]}}, u, {"birria": 10}, 10,
                          {"tulang": {"qty": 20}}, {"beef": 12}, {"beef": {"name": "Beef", "unit": "kg"}})
    birria, tulang = r["lines"]
    assert (birria["target"], birria["batches"], birria["source"]) == (67, 4, "usage")      # 70 x 1.1 - 10 on hand = 67; 67/17 -> 4 batches
    assert (tulang["target"], tulang["source"]) == (20, "manual")
    assert r["ingredients"] == [{"item_id": "beef", "name": "Beef", "unit": "kg", "needed": 20.0, "on_hand": 12, "to_buy": 8}]


def test_reorder_flags_large_changes_and_counts_open_orders():
    u = Usage([{"date": day(7), "kind": "use", "qty": -100, "location_id": "k", "item_id": "bread"}], TODAY, 1)
    r = reorder([{"_key": "bread", "name": "Bread", "supplier_id": "bk"}], u, {"bread": 20}, {"bread": 30}, 0, {"bread": 20}, 30)
    line = r["lines"][0]
    assert (line["recommended"], line["previous"], line["large_change"]) == (50, 20, True)
    out = warehouse_out([{"_key": "bread"}], u, "k", {"bread": 10}, {"bread": 40}, 3)
    assert out["lines"][0]["suggested"] == 33                                       # 100/7 x 3 = 42.9 - 10 -> 33


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC",
                                       "settings": {"target_weeks": 1, "safety_pct": 0, "large_change_pct": 30}})
    harness.seed("locations", "wh", {"tenant_id": "hft", "kind": "warehouse", "holding": True, "active": True, "days_of_cover": 3})
    harness.seed("locations", "k1", {"tenant_id": "hft", "kind": "kitchen", "holding": False, "active": True, "days_of_cover": 2})
    harness.seed("locations", "s1", {"tenant_id": "hft", "kind": "store", "holding": False, "active": True, "days_of_cover": 2})
    harness.seed("items", "bread", {"tenant_id": "hft", "name": "Bread", "kind": "ingredient", "unit": "loaf", "supplier_id": "bk", "active": True})
    harness.seed("items", "birria", {"tenant_id": "hft", "name": "Birria", "kind": "finished", "unit": "box", "active": True})
    harness.seed("recipes", "birria", {"tenant_id": "hft", "batch_output": 10, "ingredients": [{"item_id": "bread", "qty": 2}]})
    harness.seed("stock_movements", "m1", {"tenant_id": "hft", "date": day(7), "kind": "count", "qty": -35, "location_id": "s1", "item_id": "birria"})
    harness.seed("stock_movements", "m2", {"tenant_id": "hft", "date": day(5), "kind": "use", "qty": -70, "location_id": "k1", "item_id": "bread"})
    harness.seed("stock_levels", "wh:bread", {"tenant_id": "hft", "location_id": "wh", "item_id": "bread", "qty": 30})
    harness.seed("purchase_orders", "po1", {"tenant_id": "hft", "state": "saved", "lines": [{"item_id": "bread", "qty": 10}]})
    return harness


def call(h, **fields):
    return h.call(T, "planning-service", {"tenant_id": "hft", **fields})


def test_service_end_to_end(h):
    t = call(h, action="PRODUCTION_TARGET", location_id="k1")
    assert t.ok and t.fields["plan"]["lines"][0]["target"] == 35 and t.fields["plan"]["lines"][0]["batches"] == 4
    assert call(h, action="PRODUCTION_TARGET", location_id="s1").reason == "NOT_A_KITCHEN"
    assert call(h, action="SET_TARGET", item_id="birria", extra=10).ok
    assert call(h, action="PRODUCTION_TARGET", location_id="k1").fields["plan"]["lines"][0]["target"] == 45    # event week (Q12)
    out = call(h, action="WAREHOUSE_OUT", to_location_id="k1")
    assert out.ok and out.fields["plan"]["lines"][0]["suggested"] == 20 and out.fields["plan"]["from_location_id"] == "wh"
    r = call(h, action="REORDER", location_id="wh")
    assert r.ok and r.fields["plan"]["lines"][0]["recommended"] == 30            # 70 - 30 on hand - 10 on order
    assert call(h, action="REORDER", location_id="k1").reason == "NOT_HOLDING_LOCATION"
    assert call(h, action="WAREHOUSE_IN", location_id="wh").ok
    assert call(h, action="PRODUCTION_TARGET", tenant_id="other", location_id="k1").reason == "UNKNOWN_BUSINESS"
