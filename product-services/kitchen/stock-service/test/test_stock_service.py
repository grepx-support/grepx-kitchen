# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""stock-service: every change moves stock and leaves a movement with who, when, why and cost."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import apply, clean_lines
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "stock_requests"


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    for tenant in ("hft", "cafe"):
        harness.seed("businesses", tenant, {"business_id": tenant, "tenant_id": tenant, "timezone": "Australia/Sydney"})
    harness.seed("locations", "wh", {"tenant_id": "hft", "kind": "warehouse", "holding": True, "active": True})
    harness.seed("locations", "k1", {"tenant_id": "hft", "kind": "kitchen", "holding": False, "active": True})
    harness.seed("locations", "s1", {"tenant_id": "hft", "kind": "store", "holding": False, "active": True})
    harness.seed("locations", "s2", {"tenant_id": "hft", "kind": "store", "holding": False, "active": True})
    harness.seed("locations", "c1", {"tenant_id": "cafe", "kind": "store", "holding": True, "active": True})
    harness.seed("items", "beef", {"tenant_id": "hft", "kind": "ingredient", "unit": "kg", "cost": 12})
    harness.seed("items", "birria", {"tenant_id": "hft", "kind": "finished", "unit": "box", "cost": 6})
    harness.seed("items", "milk", {"tenant_id": "cafe", "kind": "ingredient", "unit": "l", "cost": 2})
    return harness


def call(h, **fields):
    return h.call(T, "stock-service", {"actor_id": "u1", "actor_name": "Sam", **fields})


def qty(h, location, item):
    return (h.read.accepted_one("stock_levels", f"{location}:{item}") or {}).get("qty", 0)


def test_rules():
    assert clean_lines([{"item_id": "a", "qty": 1}, {"item_id": "a", "qty": "2.5"}, {"item_id": "b", "qty": 0}]) == [{"item_id": "a", "qty": 3.5}]
    with pytest.raises(ValueError, match="NO_LINES"):
        clean_lines([])
    after, moves = apply({"x:a": 5}, [{"location_id": "x", "item_id": "a", "kind": "count", "set": 3}])
    assert after == {"x:a": 3} and moves[0]["qty"] == -2 and moves[0]["before"] == 5


def test_daily_flow(h):
    assert call(h, action="RECEIVE", tenant_id="hft", location_id="wh", lines=[{"item_id": "beef", "qty": 20}], ref="po-1").ok
    v = call(h, action="SEND", tenant_id="hft", from_location_id="wh", to_location_id="k1", lines=[{"item_id": "beef", "qty": 8}])
    assert v.ok and (qty(h, "wh", "beef"), qty(h, "k1", "beef")) == (12, 8)
    assert call(h, action="USE", tenant_id="hft", location_id="k1", lines=[{"item_id": "beef", "qty": 4.5}]).ok
    assert call(h, action="PRODUCE", tenant_id="hft", location_id="k1", lines=[{"item_id": "birria", "qty": 10}]).ok
    assert call(h, action="SEND", tenant_id="hft", from_location_id="k1", to_location_id="s1",
                lines=[{"item_id": "birria", "qty": 10}]).reason == "NOT_HOLDING_LOCATION"
    assert call(h, action="TRANSFER", tenant_id="hft", from_location_id="k1", to_location_id="s1", lines=[{"item_id": "birria", "qty": 10}]).ok
    assert call(h, action="TRANSFER", tenant_id="hft", from_location_id="s1", to_location_id="s2", lines=[{"item_id": "birria", "qty": 3}]).ok
    assert (qty(h, "s1", "birria"), qty(h, "s2", "birria")) == (7, 3)
    c = call(h, action="COUNT", tenant_id="hft", location_id="s1", lines=[{"item_id": "birria", "qty": 2}], ref="closing-1")
    assert c.ok and c.fields["changes"][0]["qty"] == -5 and qty(h, "s1", "birria") == 2
    moves = h.rows("stock_movements", tenant_id="hft")
    count = [m for m in moves if m["kind"] == "count"][0]
    assert (count["user_name"], count["ref"], count["value"], count["before"], count["after"]) == ("Sam", "closing-1", -30, 7, 2)
    assert {m["kind"] for m in moves} == {"receive", "send_out", "send_in", "use", "produce", "transfer_out", "transfer_in", "count"}


def test_rules_at_the_edges(h):
    assert call(h, action="PRODUCE", tenant_id="hft", location_id="s1", lines=[{"item_id": "birria", "qty": 1}]).reason == "NOT_A_KITCHEN"
    assert call(h, action="PRODUCE", tenant_id="hft", location_id="k1", lines=[{"item_id": "beef", "qty": 1}]).reason == "NOT_FINISHED_GOOD"
    assert call(h, action="ADJUST", tenant_id="hft", location_id="s1", lines=[{"item_id": "beef", "qty": 1}]).reason == "REASON_REQUIRED"
    a = call(h, action="ADJUST", tenant_id="hft", location_id="s1", lines=[{"item_id": "beef", "qty": 0}], note="miscounted yesterday")
    assert a.ok
    assert call(h, action="TRANSFER", tenant_id="hft", from_location_id="s1", to_location_id="s1",
                lines=[{"item_id": "beef", "qty": 1}]).reason == "SAME_LOCATION"
    assert call(h, action="RECEIVE", tenant_id="hft", location_id="wh", lines=[]).reason == "NO_LINES"
    assert call(h, action="RECEIVE", tenant_id="hft", location_id="wh", lines=[{"item_id": "beef", "qty": -1}]).reason == "INVALID_QUANTITY"
    # BUS-05: one business can never touch another's locations or items
    assert call(h, action="RECEIVE", tenant_id="cafe", location_id="wh", lines=[{"item_id": "milk", "qty": 1}]).reason == "UNKNOWN_LOCATION"
    assert call(h, action="RECEIVE", tenant_id="cafe", location_id="c1", lines=[{"item_id": "beef", "qty": 1}]).reason == "UNKNOWN_ITEM"
    assert call(h, action="RECEIVE", tenant_id="", location_id="c1", lines=[{"item_id": "milk", "qty": 1}]).reason == "MISSING_TENANT"


def test_a_closing_without_counts_still_closes_the_day(h):
    v = call(h, action="COUNT", tenant_id="hft", location_id="s1", lines=[], ref="closing-2")
    assert v.ok and v.fields["movements"] == 0


def test_a_warehouse_out_is_a_delivery_until_the_destination_confirms_it(h):
    call(h, action="RECEIVE", tenant_id="hft", location_id="wh", lines=[{"item_id": "beef", "qty": 10}])
    sent = call(h, action="SEND", tenant_id="hft", from_location_id="wh", to_location_id="s1", lines=[{"item_id": "beef", "qty": 4}])
    trip = h.rows("deliveries")[0]
    assert sent.ok and (trip["state"], trip["to_location_id"], trip["lines"], trip["sent_by"]) == ("sent", "s1", 1, "Sam")
    done = call(h, action="DELIVERED", tenant_id="hft", delivery_id=trip["_key"])
    assert done.ok and h.rows("deliveries")[0]["state"] == "delivered" and qty(h, "s1", "beef") == 4   # stock moved once
    assert call(h, action="DELIVERED", tenant_id="hft", delivery_id=trip["_key"]).reason == "ALREADY_DELIVERED"
    assert call(h, action="DELIVERED", tenant_id="cafe", delivery_id=trip["_key"]).reason == "UNKNOWN_DELIVERY"
