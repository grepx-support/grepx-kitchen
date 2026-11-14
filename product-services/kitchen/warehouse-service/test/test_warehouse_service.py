# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""warehouse-service: lots follow stock first-expiry-first-out, bins, putaway, pick lists that become a warehouse-out."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness
from nexus_api import NexusApplication, Row
from nexus_testkit import MemoryClient

from domain import allocate, follow, take
from jobs import follow_stock
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "warehouse_requests"


def lot(lot_id, qty, expiry=None, received="2026-11-01", **more):
    return {"lot_id": lot_id, "qty": qty, "expiry": expiry, "received": received, "location_id": "wh", "item_id": "beef", **more}


# ---------------- domain ----------------
def test_take_uses_the_first_expiry_first_and_a_named_lot_before_that():
    lots = [lot("late", 5, "2026-12-01"), lot("none", 5), lot("soon", 2, "2026-11-12")]
    parts, short = take(lots, 4)
    assert [(l["lot_id"], n) for l, n in parts] == [("soon", 2), ("late", 2)] and short == 0
    assert [l["lot_id"] for l, _ in take(lots, 1, prefer="none")[0]] == ["none"]
    assert take(lots, 20)[1] == 8


def test_follow_moves_lots_with_the_stock():
    lots = {("wh", "beef"): [lot("a", 3, "2026-11-20", lot_code="B7"), lot("b", 10, "2026-11-30")]}
    items = {"beef": {"shelf_life_days": 5, "cost": 12}}
    sent = follow("r1", {"tenant_id": "hft", "lines": [{"item_id": "beef", "qty": 5}]},
                  [{"location_id": "wh", "item_id": "beef", "kind": "send_out", "qty": -5},
                   {"location_id": "s1", "item_id": "beef", "kind": "send_in", "qty": 5}], lots, items, "2026-11-10")
    by = {l["lot_id"]: l for l in sent}
    assert (by["a"]["qty"], by["a"]["open"], by["b"]["qty"]) == (0, False, 8)
    arrived = [l for l in sent if l["location_id"] == "s1"]
    assert [(l["qty"], l["expiry"], l["lot_code"]) for l in arrived] == [(3, "2026-11-20", "B7"), (2, "2026-11-30", "")]
    got = follow("r2", {"tenant_id": "hft", "lines": [{"item_id": "beef", "qty": 4, "expiry": "2026-12-24", "bin_id": "A1"}]},
                 [{"location_id": "wh", "item_id": "beef", "kind": "receive", "qty": 4}], {}, items, "2026-11-10")
    assert (got[0]["lot_id"], got[0]["expiry"], got[0]["bin_id"], got[0]["unit_cost"]) == ("r2-0", "2026-12-24", "A1", 12)
    made = follow("r3", {"tenant_id": "hft", "lines": []}, [{"location_id": "k", "item_id": "beef", "kind": "produce", "qty": 2}], {}, items, "2026-11-10")
    assert made[0]["expiry"] == "2026-11-15"                              # shelf life from the item
    assert follow("r3", {"tenant_id": "hft"}, [{"location_id": "k", "item_id": "beef", "kind": "produce", "qty": 2}], {}, items, "2026-11-10") == made


def test_allocate_names_bins_and_what_is_missing():
    lots, short = allocate([lot("a", 2, "2026-11-20", bin_id="C-01")], 5)
    assert lots == [{"lot_id": "a", "bin_id": "C-01", "expiry": "2026-11-20", "qty": 2}] and short == 3


# ---------------- service ----------------
@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    for tenant in ("hft", "cafe"):
        harness.seed("businesses", tenant, {"business_id": tenant, "tenant_id": tenant})
    harness.seed("locations", "wh", {"tenant_id": "hft", "kind": "warehouse", "holding": True, "active": True})
    harness.seed("locations", "s1", {"tenant_id": "hft", "kind": "store", "active": True})
    harness.seed("locations", "c1", {"tenant_id": "cafe", "kind": "store", "active": True})
    harness.seed("items", "beef", {"tenant_id": "hft", "name": "Beef", "unit": "kg", "cost": 12, "shelf_life_days": 6})
    return harness


def call(h, **fields):
    return h.call(T, "warehouse-service", {"actor_id": "u1", "actor_name": "Wes", **fields})


def test_bins_and_putaway_stay_inside_the_business_and_location(h):
    b = call(h, action="SAVE_BIN", tenant_id="hft", location_id="wh", code=" a-01 ", zone="chilled")
    assert b.ok and b.fields["bin"]["code"] == "A-01"
    assert call(h, action="SAVE_BIN", tenant_id="cafe", location_id="wh", code="X").reason == "UNKNOWN_LOCATION"
    assert call(h, action="SAVE_BIN", tenant_id="hft", location_id="wh", code="X", zone="hot").reason == "INVALID_ZONE"
    h.seed("lots", "L1", {"tenant_id": "hft", "location_id": "wh", "item_id": "beef", "qty": 4, "open": True})
    assert call(h, action="MOVE_LOT", tenant_id="hft", lot_id="L1", bin_id=b.fields["bin"]["bin_id"]).ok
    assert h.rows("lots")[0]["bin_id"] == b.fields["bin"]["bin_id"]
    other = call(h, action="SAVE_BIN", tenant_id="hft", location_id="s1", code="S")
    assert call(h, action="MOVE_LOT", tenant_id="hft", lot_id="L1", bin_id=other.fields["bin"]["bin_id"]).reason == "UNKNOWN_BIN"


def test_a_pick_list_becomes_one_warehouse_out(h):
    h.seed("lots", "L1", {"tenant_id": "hft", "location_id": "wh", "item_id": "beef", "qty": 3, "expiry": "2026-11-12", "bin_id": "A", "open": True})
    h.seed("lots", "L2", {"tenant_id": "hft", "location_id": "wh", "item_id": "beef", "qty": 9, "expiry": "2026-11-30", "bin_id": "B", "open": True})
    p = call(h, action="CREATE_PICK", tenant_id="hft", from_location_id="wh", to_location_id="s1", lines=[{"item_id": "beef", "qty": 5}])
    line = p.fields["pick"]["lines"][0]
    assert p.ok and [x["lot_id"] for x in line["lots"]] == ["L1", "L2"] and line["short"] == 0
    pid = p.fields["pick"]["pick_id"]
    assert call(h, action="COMPLETE_PICK", tenant_id="hft", pick_id=pid).reason == "NOTHING_PICKED"
    assert call(h, action="PICK", tenant_id="hft", pick_id=pid, item_id="beef", qty=5).ok
    assert call(h, action="COMPLETE_PICK", tenant_id="hft", pick_id=pid).ok
    send = h.rows("stock_requests")[0]
    assert (send["action"], send["from_location_id"], send["lines"][0]["qty"], send["ref"]) == ("SEND", "wh", 5, pid)
    assert call(h, action="PICK", tenant_id="hft", pick_id=pid, item_id="beef", qty=1).reason == "PICK_CLOSED"
    assert call(h, action="CANCEL_PICK", tenant_id="cafe", pick_id=pid).reason == "UNKNOWN_PICK"


def test_following_an_accepted_stock_change_happens_once(h):
    app = NexusApplication(MemoryClient(h.engine), "x")
    row = Row("rq1", {"tenant_id": "hft", "action": "RECEIVE", "date": "2026-11-10", "lines": [{"item_id": "beef", "qty": 4}],
                      "changes": [{"location_id": "wh", "item_id": "beef", "kind": "receive", "qty": 4}]})
    assert follow_stock(app, row, cfg) == "followed"
    assert follow_stock(app, row, cfg) == "skipped"
    lots = h.rows("lots")
    assert len(lots) == 1 and (lots[0]["qty"], lots[0]["expiry"]) == (4, "2026-11-16")
