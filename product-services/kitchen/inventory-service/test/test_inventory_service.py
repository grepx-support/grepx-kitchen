# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""inventory-service: par levels, alerts kept once a day and sent to the owners, stock takes, valuation, ABC."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from nexus_testkit import MemoryClient

from domain import abc, alerts, clean_par, consumption, cover, valuation, variance
from jobs import handle_tick
from routes import handle
from routes.common import Stock

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "inventory_requests"


# ---------------- domain ----------------
def test_par_levels_and_alerts():
    assert clean_par({"min": "5", "max": 12}) == {"min": 5, "max": 12}
    with pytest.raises(ValueError):
        clean_par({"min": 5, "max": 2})
    levels = [{"location_id": "wh", "item_id": "beef", "qty": 3}, {"location_id": "s1", "item_id": "beef", "qty": -1},
              {"location_id": "wh", "item_id": "milk", "qty": 9}]
    lots = [{"lot_id": "l1", "location_id": "wh", "item_id": "milk", "qty": 4, "expiry": "2026-11-11"},
            {"lot_id": "l2", "location_id": "wh", "item_id": "milk", "qty": 5, "expiry": "2026-11-09"},
            {"lot_id": "l3", "location_id": "wh", "item_id": "milk", "qty": 0, "expiry": "2026-11-01"}]
    got = alerts("2026-11-10", levels, {("wh", "beef"): {"min": 5, "max": 10}}, lots)
    assert sorted(a["kind"] for a in got) == ["expired", "expiring", "low", "negative"]
    assert next(a for a in got if a["kind"] == "low")["fill_to"] == 10


def test_variance_valuation_abc_cover():
    v = variance([{"item_id": "beef", "expected": 10, "counted": 8}, {"item_id": "milk", "expected": 2, "counted": None}], {"beef": 12})
    assert v == [{"item_id": "beef", "expected": 10, "counted": 8, "variance": -2, "value": -24}]
    val = valuation([{"location_id": "wh", "item_id": "beef", "qty": 10}], {"beef": 12},
                    [{"location_id": "wh", "item_id": "beef", "qty": 4, "unit_cost": 10}])
    assert (val[0]["value"], val[0]["lot_value"]) == (120, 40 + 6 * 12)
    moves = [{"kind": "count", "item_id": "beef", "qty": -8, "value": -96, "location_id": "s1"},
             {"kind": "waste", "item_id": "milk", "qty": -1, "value": -2, "location_id": "s1"},
             {"kind": "use", "item_id": "taco", "qty": -5, "value": -30, "location_id": "k1"},       # kitchen making food: not consumed here
             {"kind": "receive", "item_id": "beef", "qty": 50, "value": 600, "location_id": "wh"}]
    used = consumption(moves, kitchens={"k1"}, finished={"taco"})
    assert set(used) == {"beef", "milk"} and abc(used) == {"beef": "A", "milk": "C"}
    assert cover({"beef": 16, "milk": 0}, used, 4) == {"beef": 8.0, "milk": 0.0}


# ---------------- service ----------------
@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "name": "HFT"})
    harness.seed("businesses", "cafe", {"business_id": "cafe", "tenant_id": "cafe", "timezone": "UTC"})
    harness.seed("locations", "wh", {"tenant_id": "hft", "name": "Warehouse", "kind": "warehouse"})
    harness.seed("items", "beef", {"tenant_id": "hft", "name": "Beef", "unit": "kg", "cost": 12, "kind": "ingredient"})
    harness.seed("stock_levels", "wh:beef", {"tenant_id": "hft", "location_id": "wh", "item_id": "beef", "qty": 3})
    harness.seed("user_access", "u1", {"staff_role_id": "hft.owner"})
    harness.seed("people", "u1", {"tenant_id": "hft", "name": "Olivia Owner", "email": "o@x.test", "phone": "+61400000001"})
    return harness


def call(h, **fields):
    return h.call(T, "inventory-service", {"actor_id": "u1", "actor_name": "Olivia", **fields})


def test_alerts_are_kept_once_a_day_and_go_to_the_owners(h):
    assert call(h, action="SET_PAR", tenant_id="hft", location_id="wh", item_id="beef", min=5, max=10).ok
    assert call(h, action="SET_PAR", tenant_id="cafe", location_id="wh", item_id="beef", min=5).reason == "UNKNOWN_LOCATION"
    first = call(h, action="CHECK_ALERTS", tenant_id="hft")
    assert first.ok and first.fields["new"] == 1 and call(h, action="CHECK_ALERTS", tenant_id="hft").fields["new"] == 0
    sent = h.rows("notifications")
    assert {n["channel"] for n in sent} == {"email", "whatsapp"} and sent[0]["template"] == "stock_alert" and sent[0]["tenant_id"] == "hft"
    alert = h.rows("alerts")[0]
    assert (alert["kind"], alert["item_name"], alert["location_name"]) == ("low", "Beef", "Warehouse")
    assert call(h, action="ACK_ALERT", tenant_id="hft", alert_id=alert["_key"]).fields["alert"]["state"] == "done"


def test_stock_take_corrects_stock_and_keeps_the_variance(h):
    take = call(h, action="START_TAKE", tenant_id="hft", location_id="wh").fields["take"]
    assert [l["expected"] for l in take["lines"]] == [3]
    assert call(h, action="START_TAKE", tenant_id="hft", location_id="wh").reason == "TAKE_OPEN_HERE"
    assert call(h, action="FINISH_TAKE", tenant_id="hft", take_id=take["take_id"]).reason == "NOTHING_COUNTED"
    call(h, action="COUNT_TAKE", tenant_id="hft", take_id=take["take_id"], lines=[{"item_id": "beef", "qty": 2}])
    done = call(h, action="FINISH_TAKE", tenant_id="hft", take_id=take["take_id"]).fields["take"]
    assert (done["state"], done["variance_value"], done["lines_changed"]) == ("done", -12, 1)
    adjust = h.rows("stock_requests")[0]
    assert (adjust["action"], adjust["lines"], adjust["note"][:10]) == ("ADJUST", [{"item_id": "beef", "qty": 2}], "Stock take")


def test_valuation_analysis_and_the_hourly_tick(h):
    v = call(h, action="VALUATION", tenant_id="hft")
    assert v.fields["total"] == 36
    a = call(h, action="ANALYSIS", tenant_id="hft", days=30)
    assert a.ok and a.fields["items"][0]["name"] == "Beef"
    call(h, action="SET_PAR", tenant_id="hft", location_id="wh", item_id="beef", min=5)
    app = NexusApplication(MemoryClient(h.engine), "x")
    assert handle_tick(app, Row("t1", {"job": "inventory-alerts", "status": "NEW"}), cfg) == 1
    assert handle_tick(app, Row("t2", {"job": "other", "status": "NEW"}), cfg) == 0
    assert Stock(h.read, "hft").today()


def test_finished_goods_thrown_away_are_valued_at_their_cost_in_the_waste_report():
    from domain import waste_by_reason
    moves = [{"kind": "waste", "item_id": "milk", "qty": -1, "value": -2, "waste_reason": "spoiled"},
             {"kind": "waste", "item_id": "taco", "qty": -3, "value": 0, "waste_reason": "overproduced"},
             {"kind": "use", "item_id": "milk", "qty": -5, "value": -10}]
    assert waste_by_reason(moves, {"milk": 2, "taco": 5}) == {"spoiled": 2, "overproduced": 15}


def test_valuation_survives_a_level_below_zero():
    from domain import valuation
    got = valuation([{"location_id": "w", "item_id": "a", "qty": -2}, {"location_id": "w", "item_id": "b", "qty": 1}],
                    {"a": 5.0, "b": 2.0}, [{"location_id": "w", "item_id": "b", "qty": 4, "unit_cost": 3}])
    assert [(r["value"], r["lot_value"]) for r in got] == [(-10.0, 0.0), (2.0, 3.0)]
