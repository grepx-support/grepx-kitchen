# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""purchase-service: save, change, copy, cancel and receive orders; receipt asks stock-service to add the stock."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import message, received_lines
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "purchase_requests"


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "name": "HFT"})
    harness.seed("locations", "wh", {"tenant_id": "hft", "name": "Warehouse", "kind": "warehouse", "holding": True, "active": True})
    harness.seed("locations", "s1", {"tenant_id": "hft", "name": "Store", "kind": "store", "holding": False, "active": True})
    harness.seed("suppliers", "bakery", {"tenant_id": "hft", "name": "Good Bakery", "phone": "+61400"})
    harness.seed("items", "bread", {"tenant_id": "hft", "name": "Bread", "unit": "loaf", "kind": "ingredient", "cost": 3})
    harness.seed("items", "lids", {"tenant_id": "hft", "name": "Lids", "unit": "pack", "kind": "supply", "cost": 9})
    return harness


def call(h, **fields):
    return h.call(T, "purchase-service", {"tenant_id": "hft", "actor_id": "u1", "actor_name": "Wes", **fields})


def test_rules():
    assert received_lines([{"item_id": "a", "qty": 5}], None) == [{"item_id": "a", "qty": 5}]
    assert received_lines([{"item_id": "a", "qty": 5}], [{"item_id": "a", "qty": 4}, {"item_id": "b", "qty": 0}]) == [{"item_id": "a", "qty": 4}]
    text = message("HFT", "Good Bakery", "PO-0001", "Warehouse", [{"item_id": "bread", "qty": 40}], {"bread": {"name": "Bread", "unit": "loaf"}})
    assert "- Bread: 40 loaf" in text and text.startswith("Order PO-0001 from HFT")


def test_order_lifecycle(h):
    v = call(h, action="SAVE", supplier_id="bakery", location_id="wh", lines=[{"item_id": "bread", "qty": 40, "recommended": 36}])
    assert v.ok and v.fields["order"]["number"] == "PO-0001" and "Bread: 40 loaf" in v.fields["order"]["text"]
    po = v.fields["order"]["po_id"]
    changed = call(h, action="SAVE", po_id=po, lines=[{"item_id": "bread", "qty": 50}, {"item_id": "lids", "qty": 2}])   # ORD-03 add items
    assert changed.ok and len(changed.fields["order"]["lines"]) == 2 and changed.fields["order"]["number"] == "PO-0001"
    copy = call(h, action="COPY", po_id=po)
    assert copy.ok and copy.fields["order"]["number"] == "PO-0002"
    assert call(h, action="CANCEL", po_id=copy.fields["order"]["po_id"]).ok
    got = call(h, action="RECEIVE", po_id=po, lines=[{"item_id": "bread", "qty": 48}, {"item_id": "lids", "qty": 2}])
    assert got.ok and got.fields["order"]["state"] == "received"
    sent = h.rows("stock_requests")
    assert len(sent) == 1 and sent[0]["lines"] == [{"item_id": "bread", "qty": 48}, {"item_id": "lids", "qty": 2}]
    assert sent[0]["location_id"] == "wh" and sent[0]["to_service"] == "stock-service"
    assert call(h, action="SAVE", po_id=po, lines=[{"item_id": "bread", "qty": 1}]).reason == "ALREADY_CLOSED"
    assert call(h, action="CANCEL", po_id=po).reason == "ALREADY_CLOSED"


def test_orders_arrive_at_a_holding_place(h):
    assert call(h, action="SAVE", supplier_id="bakery", location_id="s1", lines=[{"item_id": "bread", "qty": 1}]).reason == "NOT_HOLDING_LOCATION"
    assert call(h, action="SAVE", supplier_id="bakery", location_id="wh", lines=[]).reason == "NO_LINES"
    assert call(h, action="SAVE", supplier_id="nobody", location_id="wh", lines=[{"item_id": "bread", "qty": 1}]).reason == "UNKNOWN_SUPPLIER"
    assert call(h, action="SAVE", tenant_id="other", supplier_id="bakery", location_id="wh",
                lines=[{"item_id": "bread", "qty": 1}]).reason == "UNKNOWN_BUSINESS"


def test_an_order_is_sent_to_its_supplier(h):
    po = call(h, action="SAVE", supplier_id="bakery", location_id="wh", lines=[{"item_id": "bread", "qty": 40}]).fields["order"]["po_id"]
    assert call(h, action="SEND", po_id=po, channels=["fax"]).reason == "INVALID_CHANNEL"
    assert call(h, action="SEND", po_id=po, channels=["email"]).reason == "NO_CONTACT"          # the bakery has a phone, no email
    done = call(h, action="SEND", po_id=po, channels=["whatsapp", "sms"])
    assert done.ok and done.fields["order"]["sent"][0]["channels"] == ["whatsapp", "sms"]
    msgs = h.rows("notifications")
    assert {m["channel"] for m in msgs} == {"whatsapp", "sms"} and msgs[0]["template"] == "purchase_order" and "Bread" in msgs[0]["values"]["text"]


def test_big_orders_wait_for_the_owner(h):
    from domain import approval_for
    assert approval_for(100, 0, None) is None and approval_for(100, 500, None) is None
    assert approval_for(600, 500, {"state": "approved", "value": 700}) == {"state": "approved", "value": 700}
    assert approval_for(800, 500, {"state": "approved", "value": 700})["state"] == "pending"           # grew past what was approved
    h.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "name": "HFT", "settings": {"po_approval_over": 100}})
    small = call(h, action="SAVE", supplier_id="bakery", location_id="wh", lines=[{"item_id": "bread", "qty": 10}]).fields["order"]
    assert small["value"] == 30 and small["approval"] is None
    big = call(h, action="SAVE", supplier_id="bakery", location_id="wh", lines=[{"item_id": "lids", "qty": 20}]).fields["order"]
    assert big["approval"] == {"state": "pending", "value": 180.0, "limit": 100.0}
    assert call(h, action="SEND", po_id=big["po_id"], channels=["whatsapp"]).reason == "NEEDS_APPROVAL"
    assert call(h, action="APPROVE", po_id=big["po_id"], approve=False).reason == "NOTE_REQUIRED"
    assert call(h, action="APPROVE", po_id=small["po_id"], approve=True).reason == "NOTHING_TO_APPROVE"
    yes = call(h, action="APPROVE", po_id=big["po_id"], approve=True, actor_name="Omar").fields["order"]["approval"]
    assert (yes["state"], yes["by"]) == ("approved", "Omar")
    assert call(h, action="SEND", po_id=big["po_id"], channels=["whatsapp"]).ok
    more = call(h, action="SAVE", po_id=big["po_id"], lines=[{"item_id": "lids", "qty": 30}]).fields["order"]
    assert more["approval"]["state"] == "pending"                                                     # 270 > the 180 approved
