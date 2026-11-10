# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""costing-service: COGS per count period, costing average, and a monthly summary that never invents a profit."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from nexus_testkit import MemoryClient

from domain import cost_day, month_summary, overhead_share
from jobs import handle_count
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "costing_requests"
SETTINGS = {"cogs_min": 25, "cogs_max": 35}


def test_cost_rules():
    assert overhead_share({"labour": 3000, "rent": 1500, "other": None}, "2026-11", 3) == {"labour": 300.0, "rent": 150.0, "other": None}
    moves = [{"kind": "count", "qty": -10, "value": -60, "unit_cost": 6, "item_id": "birria"},
             {"kind": "count", "qty": 1, "value": 2, "unit_cost": 2, "item_id": "lime"},
             {"kind": "use", "qty": -2, "value": -24, "unit_cost": 12, "item_id": "beef"},
             {"kind": "receive", "qty": 50, "value": 300, "unit_cost": 6, "item_id": "birria"}]
    d = cost_day({"date": "2026-11-09", "total_sales": 200}, "2026-11-08", moves, False, {"labour": 3000, "rent": 900, "other": 300}, SETTINGS)
    assert (d["ingredient_cost"], d["cogs_pct"], d["period_days"]) == (82, 41.0, 1) and d["out_of_range"]
    assert d["costing_pct"] == round((82 + 100 + 30 + 10) / 200 * 100, 1) and d["missing"] == []
    k = cost_day({"date": "2026-11-09", "total_sales": 0}, None, moves, True, None, SETTINGS)
    assert k["ingredient_cost"] == 58 and k["cogs_pct"] is None and k["missing"] == ["labour", "rent", "other"]


def test_month_summary_never_shows_profit_with_a_missing_cost():
    days = [{"sales": 1000, "ingredient_cost": 300, "out_of_range": False}, {"sales": 500, "ingredient_cost": 200, "out_of_range": True}]
    full = month_summary(days, {"s1": {"labour": 400, "rent": 200, "other": 50}}, "2026-11", SETTINGS)
    assert full["net_profit"] == 350 and full["complete"] and full["days_out_of_range"] == 1
    gap = month_summary(days, {"s1": {"labour": 400, "rent": 200, "other": 50}, "s2": None}, "2026-11", SETTINGS)
    assert gap["net_profit"] is None and gap["missing"] == ["labour", "rent", "other"] and gap["sales"] == 1500   # QR-04
    running = month_summary(days, {"s1": {"labour": 3000, "rent": 1500, "other": 0}}, "2026-11", SETTINGS, through=10)
    assert (running["labour"], running["rent"], running["overheads_days"]) == (1000, 500, 10)          # 10 of 30 days


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "currency": "AUD", "settings": SETTINGS})
    harness.seed("locations", "s1", {"tenant_id": "hft", "name": "Truck", "kind": "truck", "active": True})
    harness.seed("closings", "s1:2026-10-08", {"tenant_id": "hft", "location_id": "s1", "date": "2026-10-08", "total_sales": 300})
    harness.seed("closings", "s1:2026-10-09", {"tenant_id": "hft", "location_id": "s1", "date": "2026-10-09", "total_sales": 400})
    harness.seed("stock_movements", "m1", {"tenant_id": "hft", "location_id": "s1", "date": "2026-10-08", "kind": "count",
                                           "qty": -10, "value": -60, "unit_cost": 6, "item_id": "birria"})
    harness.seed("stock_movements", "m2", {"tenant_id": "hft", "location_id": "s1", "date": "2026-10-09", "kind": "count",
                                           "qty": -20, "value": -120, "unit_cost": 6, "item_id": "birria"})
    return harness


def test_count_reaction_overheads_and_summary(h):
    app = NexusApplication(MemoryClient(h.engine), "x")
    for day in ("2026-10-08", "2026-10-09"):
        assert handle_count(app, Row(f"count-s1:{day}", {"tenant_id": "hft", "location_id": "s1", "date": day, "ref": f"s1:{day}"}), cfg) == "computed"
    second = h.read.accepted_one("cost_days", "s1:2026-10-09")
    assert (second["ingredient_cost"], second["cogs_pct"], second["period_start"]) == (120, 30.0, "2026-10-08")   # only the 9th's count
    s = h.call(T, "costing-service", {"action": "SUMMARY", "tenant_id": "hft", "month": "2026-10"})
    assert s.ok and s.fields["summary"]["net_profit"] is None and "labour" in s.fields["summary"]["missing"]
    assert h.call(T, "costing-service", {"action": "SET_OVERHEAD", "tenant_id": "hft", "location_id": "s1", "month": "2026-10",
                                         "labour": 3000, "rent": 1500, "other": 300}).ok
    s = h.call(T, "costing-service", {"action": "SUMMARY", "tenant_id": "hft", "month": "2026-10", "location_id": "s1"}).fields["summary"]
    assert (s["sales"], s["ingredient_cost"], s["net_profit"], s["closings"]) == (700, 180, 700 - 180 - 4800, 2)
    assert h.read.accepted_one("cost_days", "s1:2026-10-09")["labour"] == round(3000 / 31, 2)   # recosted when the overhead arrived (October: 31 days)
    assert h.call(T, "costing-service", {"action": "SET_OVERHEAD", "tenant_id": "hft", "location_id": "s1", "month": "2026-13",
                                         "labour": 1, "rent": 1, "other": 1}).reason == "INVALID_MONTH"


def test_waste_is_part_of_the_cost_of_goods_everywhere():
    moves = [{"kind": "waste", "qty": -2, "unit_cost": 5, "value": -10, "item_id": "beef"},
             {"kind": "use", "qty": -1, "unit_cost": 5, "value": -5, "item_id": "beef"}]
    assert cost_day({"date": "2026-11-09", "total_sales": 100}, None, moves, True, None, SETTINGS)["ingredient_cost"] == 10    # kitchen: waste only
    assert cost_day({"date": "2026-11-09", "total_sales": 100}, None, moves, False, None, SETTINGS)["ingredient_cost"] == 15
