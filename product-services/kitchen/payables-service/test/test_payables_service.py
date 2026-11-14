# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""payables-service: three-way match, duplicate bills, approval with a note, part payments, due buckets."""
from decimal import Decimal
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import due_buckets, match
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "payables_requests"
PO = {"po_id": "po1", "number": "PO-0001", "supplier_id": "meat", "lines": [{"item_id": "beef", "qty": 10}, {"item_id": "pork", "qty": 5}],
      "received": [{"item_id": "beef", "qty": 8}, {"item_id": "pork", "qty": 5}]}


def line(item, qty, cents):
    return {"item_id": item, "qty": str(qty), "unit_price": cents}


# ---------------- rules ----------------
def test_three_way_match():
    assert match([line("beef", 8, 1200), line("pork", 5, 900)], PO, {"beef": 1200, "pork": 900}) == ("matched", [])
    state, issues = match([line("beef", 10, 1200), line("pork", 5, 990), line("lamb", 1, 100)], PO, {"beef": 1200, "pork": 900})
    assert state == "check"
    assert [i["issue"] for i in issues] == ["more_than_received", "price_differs", "not_ordered"]
    assert match([line("beef", 8, 1220)], PO, {"beef": 1200}, tolerance=Decimal(2))[0] == "matched"      # +1.7 %: within 2 %
    assert match([line("beef", 1, 1)], {**PO, "received": []}, {})[1][0]["issue"] == "not_received_yet"
    assert match([{"item_id": "", "qty": "1", "unit_price": 500}], None, {}) == ("no_order", [])


def test_due_buckets():
    bills = [{"state": "approved", "due": "2026-11-01", "total": 100, "paid": 0}, {"state": "entered", "due": "2026-11-15", "total": 50, "paid": 20},
             {"state": "approved", "due": "2026-12-30", "total": 10, "paid": 0}, {"state": "paid", "due": "2026-11-01", "total": 99, "paid": 99}]
    assert due_buckets(bills, "2026-11-13") == {"overdue": 100, "this_week": 30, "later": 10}


# ---------------- service ----------------
@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "currency": "SGD"})
    harness.seed("businesses", "cafe", {"business_id": "cafe", "tenant_id": "cafe", "timezone": "UTC"})
    harness.seed("suppliers", "meat", {"tenant_id": "hft", "name": "Harbour Meats"})
    harness.seed("suppliers", "veg", {"tenant_id": "hft", "name": "Green Valley"})
    harness.seed("items", "beef", {"tenant_id": "hft", "name": "Beef", "unit": "kg", "cost": 12})
    harness.seed("items", "pork", {"tenant_id": "hft", "name": "Pork", "unit": "kg", "cost": 9})
    harness.seed("purchase_orders", "po1", {"tenant_id": "hft", **PO})
    return harness


def call(h, **fields):
    return h.call(T, "payables-service", {"actor_id": "u1", "actor_name": "Olivia", "tenant_id": "hft", **fields})


def bill(h, **extra):
    return call(h, action="SAVE_BILL", supplier_id="meat", supplier_ref="HM-778", bill_date="2026-11-10", tax_rate=9,
                lines=[{"item_id": "beef", "qty": 8, "unit_price": "12.00"}, {"item_id": "pork", "qty": 5, "unit_price": "9"}], **extra)


def test_matched_bill_is_approved_and_paid_in_parts(h):
    saved = bill(h, po_id="po1")
    assert saved.ok, saved.reason
    b = saved.fields["bill"]
    assert (b["match"], b["total"], b["due"], b["po_number"]) == ("matched", 15369, "2026-12-10", "PO-0001")
    assert bill(h).reason == "DUPLICATE_BILL"
    key = saved.fields["bill_id"]
    assert call(h, action="RECORD_PAYMENT", bill_id=key, amount=10).reason == "NOT_APPROVED"
    assert call(h, action="APPROVE_BILL", bill_id=key).fields["bill"]["state"] == "approved"
    assert call(h, action="RECORD_PAYMENT", bill_id=key, amount="100", date="2026-11-20").fields["bill"]["paid"] == 10000
    assert call(h, action="VOID_BILL", bill_id=key).reason == "HAS_PAYMENTS"
    done = call(h, action="RECORD_PAYMENT", bill_id=key, amount="53.69", date="2026-11-21").fields["bill"]
    assert done["state"] == "paid"


def test_mismatch_needs_a_note_and_order_must_be_the_suppliers(h):
    odd = call(h, action="SAVE_BILL", supplier_id="meat", supplier_ref="HM-779", po_id="po1", lines=[{"item_id": "beef", "qty": 10, "unit_price": 15}])
    assert odd.fields["bill"]["match"] == "check" and {i["issue"] for i in odd.fields["bill"]["issues"]} == {"more_than_received", "price_differs"}
    key = odd.fields["bill_id"]
    assert call(h, action="APPROVE_BILL", bill_id=key).reason == "NOTE_REQUIRED"
    assert call(h, action="APPROVE_BILL", bill_id=key, note="Agreed price rise").fields["bill"]["approval_note"] == "Agreed price rise"
    assert call(h, action="SAVE_BILL", supplier_id="veg", supplier_ref="G1", po_id="po1", lines=[{"description": "x", "qty": 1, "unit_price": 1}]).reason \
        == "ORDER_OF_ANOTHER_SUPPLIER"
    assert call(h, action="SAVE_BILL", supplier_id="meat", supplier_ref="", lines=[]).reason == "SUPPLIER_REF_REQUIRED"
    assert call(h, action="SAVE_BILL", tenant_id="cafe", supplier_id="meat", supplier_ref="x", lines=[]).reason == "UNKNOWN_SUPPLIER"


def test_summary_lists_what_is_due(h):
    bill(h, po_id="po1", due="2020-01-01")
    s = call(h, action="SUMMARY").fields
    assert (s["to_approve"], s["due"]["overdue"], s["bills"][0]["overdue"]) == (1, 15369, True)


def test_months_count_bills_by_bill_date_and_payments():
    from domain import monthly
    rows = [{"state": "approved", "bill_date": "2026-02-10", "taxable": 3000, "tax": 270, "total": 3270, "payments": [{"date": "2026-03-01", "amount": 1000}]},
            {"state": "void", "bill_date": "2026-02-11", "taxable": 50, "tax": 0, "total": 50}]
    months = monthly(rows, 2026)
    assert (months[1]["purchases"], months[1]["tax"], months[1]["bills"], months[2]["paid"]) == (3000, 270, 1, 1000)


def test_monthly_action(h):
    bill(h)
    got = call(h, action="MONTHLY").fields
    assert sum(m["bills"] for m in got["months"]) == 1


def test_price_history_and_jumps_tell_the_owner(h):
    from domain.prices import changes, unit_cost
    assert unit_cost({"unit_price": 1000, "discount": "10"}) == 900
    h.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "currency": "SGD", "settings": {"price_jump_pct": 10}})
    h.seed("user_access", "o1", {"staff_role_id": "hft.owner"})
    h.seed("people", "o1", {"name": "Omar Owner", "email": "omar@hft.test", "phone": ""})
    assert bill(h).fields["bill"]["price_changes"] == []                                         # first bill: nothing to compare
    up = call(h, action="SAVE_BILL", supplier_id="meat", supplier_ref="HM-801", bill_date="2026-11-12",
              lines=[{"item_id": "beef", "qty": 8, "unit_price": "13.80"}, {"item_id": "pork", "qty": 5, "unit_price": "9.30"}]).fields["bill"]
    got = {c["item_id"]: c for c in up["price_changes"]}
    assert (got["beef"]["pct"], got["beef"]["jump"]) == (15.0, True) and (got["pork"]["pct"], got["pork"]["jump"]) == (3.3, False)
    sent = h.rows("notifications")
    assert len(sent) == 1 and sent[0]["template"] == "price_jump" and "Beef" in sent[0]["values"]["summary"]
    view = call(h, action="PRICES", item_id="beef", days=3650).fields
    assert [p["price"] for p in view["points"]] == [1200, 1380] and view["rises"][0]["jump"] and view["jump_pct"] == 10
    assert changes([{"item_id": "beef", "unit_price": 1380}], "veg", "2026-11-12", "x", [], 10) == []    # another supplier: no history


def test_landed_cost_spreads_and_recosts(h):
    from domain.landed import clean_costs, share
    assert share(100, [1, 1, 1]) == [34, 33, 33] or sum(share(100, [1, 1, 1])) == 100
    assert clean_costs([{"kind": "duty", "amount": "5"}])[0] == {"kind": "duty", "amount": 500, "spread": "value", "on_bill": True, "note": ""}
    saved = bill(h, landed=[{"kind": "freight", "amount": "20", "spread": "qty"}, {"kind": "duty", "amount": "10.30", "on_bill": False}])
    assert saved.ok, saved.reason
    b = saved.fields["bill"]
    beef, pork = b["lines"]
    # freight 2000 by qty 8:5 -> 1231 / 769; duty 1030 by value 9600:4500 -> 701 / 329
    assert (beef["landed"], pork["landed"]) == (1231 + 701, 769 + 329)
    assert beef["landed_unit"] == "1441.50" and b["landed_total"] == 3030 and b["total"] == 15369 + 2000
    assert call(h, action="SAVE_BILL", supplier_id="meat", supplier_ref="X1", lines=[{"item_id": "beef", "qty": 1, "unit_price": 1}],
                landed=[{"kind": "bribe", "amount": 1}]).reason == "INVALID_LANDED_COST"
    ok = call(h, action="APPROVE_BILL", bill_id=saved.fields["bill_id"])
    assert ok.fields["recosted"] == {"beef": "14.415", "pork": "11.196"}
    sent = [r for r in h.rows("item_requests")]
    assert sent and sent[-1]["costs"]["beef"] == "14.415"


def test_returns_credit_the_bill_and_leave_stock(h):
    saved = bill(h)
    key = saved.fields["bill_id"]
    assert call(h, action="RETURN_GOODS", bill_id=key, reason="damaged", lines=[{"item_id": "beef", "qty": 9}]).reason == "MORE_THAN_BILLED"
    assert call(h, action="RETURN_GOODS", bill_id=key, reason="meh", lines=[{"item_id": "beef", "qty": 1}]).reason == "INVALID_REASON"
    r = call(h, action="RETURN_GOODS", bill_id=key, reason="damaged", location_id="wh", lines=[{"item_id": "beef", "qty": 2}])
    assert r.ok, r.reason
    b = r.fields["bill"]
    assert (r.fields["return"]["credit"], b["credited"]) == (2616, 2616)       # 2 x 12.00 + 9 % tax
    assert h.rows("stock_requests")[-1]["action"] == "RETURN"
    assert call(h, action="RETURN_GOODS", bill_id=key, reason="damaged", lines=[{"item_id": "beef", "qty": 6.5}]).reason == "MORE_THAN_BILLED"
    call(h, action="APPROVE_BILL", bill_id=key)
    assert call(h, action="RECORD_PAYMENT", bill_id=key, amount="127.53", date="2026-11-20").fields["bill"]["state"] == "paid"
    back = call(h, action="RETURN_GOODS", bill_id=key, reason="quality", lines=[{"item_id": "pork", "qty": 1}]).fields["bill"]
    assert back["refund_due"] == 981
