# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""billing-service quotations: quote -> order -> invoice, every move checked against the state it starts from."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import check_open, clean_event, invoice_from, may, numbered, per_guest, view_status
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "billing_requests"
EVENT = {"event_date": "2026-12-20", "event_time": "18:30", "venue": " Marina  Hall ", "guests": "120", "event_name": "Year-end party"}


def test_event_numbers_validity_and_moves():
    assert clean_event(EVENT) == {"event_date": "2026-12-20", "event_time": "18:30", "venue": "Marina Hall", "guests": 120, "event_name": "Year-end party"}
    for bad in ({**EVENT, "event_date": ""}, {**EVENT, "event_time": "25:00"}, {**EVENT, "guests": -1}, {**EVENT, "guests": "many"}):
        with pytest.raises(ValueError, match="INVALID_EVENT"):
            clean_event(bad)
    assert numbered("Q", 2026, ["Q-2026-0004", "SO-2026-0009", "Q-2025-0010"]) == "Q-2026-0005"
    sent = {"state": "sent", "valid_until": "2026-11-20"}
    assert view_status(sent, "2026-11-21") == "expired" and view_status(sent, "2026-11-20") == "sent"
    with pytest.raises(ValueError, match="QUOTE_EXPIRED"):
        check_open(sent, "2026-11-21")
    with pytest.raises(ValueError, match="WRONG_STATE"):
        may("invoice", sent)
    assert per_guest({"total": 120000, "guests": 120}) == 1000 and per_guest({"total": 5}) == 0
    inv = invoice_from({"quote_id": "q1", "order_number": "SO-2026-0001", "customer_id": "c", "lines": [], "total": 9, "event_date": "2026-12-20"}, "i1", "now", "Olivia")
    assert (inv["state"], inv["reference"], inv["quote_id"], inv["total"]) == ("draft", "SO-2026-0001", "q1", 9)


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "name": "HFT", "currency": "SGD"})
    harness.seed("businesses", "cafe", {"business_id": "cafe", "tenant_id": "cafe", "timezone": "UTC"})
    harness.seed("items", "taco", {"tenant_id": "hft", "name": "Tacos", "unit": "box", "kind": "finished"})
    return harness


def call(h, tenant="hft", **fields):
    return h.call(T, "billing-service", {"actor_id": "u1", "actor_name": "Olivia", "tenant_id": tenant, **fields})


def test_quote_becomes_an_order_then_an_invoice(h):
    cust = call(h, action="SAVE_CUSTOMER", name="Marina Events", email="events@marina.test").fields["customer_id"]
    lines = [{"item_id": "taco", "qty": 120, "unit_price": "8"}, {"description": "Service staff (4 h)", "qty": 3, "unit_price": "120"}]
    assert call(h, action="SAVE_QUOTE", customer_id=cust, lines=lines, **{**EVENT, "event_date": ""}).reason == "INVALID_EVENT"
    assert call(h, action="SAVE_QUOTE", customer_id=cust, lines=lines, valid_days=0, **EVENT).reason == "INVALID_DATE"
    q = call(h, action="SAVE_QUOTE", customer_id=cust, lines=lines, tax_rate=9, valid_days=10, **EVENT).fields["quote"]
    assert (q["state"], q["subtotal"], q["total"], q["guests"]) == ("draft", 132000, 143880, 120)
    assert call(h, action="INVOICE_ORDER", quote_id=q["quote_id"]).reason == "WRONG_STATE"
    pdf = [{"name": "Q.pdf", "mime": "application/pdf", "data_b64": "JVBERg=="}]
    numbered_only = call(h, action="SEND_QUOTE", quote_id=q["quote_id"], number_only=True).fields["quote"]
    assert numbered_only["number"] == "Q-" + numbered_only["quoted_on"][:4] + "-0001" and numbered_only["state"] == "draft"
    sent = call(h, action="SEND_QUOTE", quote_id=q["quote_id"], send=True, attachments=pdf).fields["quote"]
    assert sent["number"] == numbered_only["number"] and len(sent["sent"]) == 1
    assert sent["number"].startswith("Q-") and sent["state"] == "sent" and sent["valid_until"] > sent["quoted_on"]
    mail = h.rows("notifications")[0]
    assert mail["template"] == "catering_quote" and mail["recipient"] == "events@marina.test" and mail["attachments"] == pdf
    again = call(h, action="SAVE_QUOTE", quote_id=q["quote_id"], customer_id=cust, lines=lines[:1], **EVENT).fields["quote"]
    assert (again["state"], again["revision"], again["number"]) == ("draft", 1, sent["number"])            # changed after sending
    call(h, action="SEND_QUOTE", quote_id=q["quote_id"])
    assert call(h, action="ACCEPT_QUOTE", quote_id=q["quote_id"], tenant="cafe").reason == "UNKNOWN_QUOTE"   # another business
    order = call(h, action="ACCEPT_QUOTE", quote_id=q["quote_id"], accepted_by="Ms Tan", customer_ref="PO 77").fields["quote"]
    assert (order["state"], order["order_number"][:3], order["accepted_by"]) == ("ordered", "SO-", "Ms Tan")
    assert call(h, action="DECLINE_QUOTE", quote_id=q["quote_id"]).reason == "WRONG_STATE"
    out = call(h, action="INVOICE_ORDER", quote_id=q["quote_id"]).fields
    assert out["quote"]["state"] == "invoiced" and out["invoice"]["state"] == "draft" and out["invoice"]["total"] == 96000          # the revised quote: 120 x 8, no tax
    issued = call(h, action="ISSUE_INVOICE", invoice_id=out["invoice_id"], issued="2026-11-14").fields["invoice"]
    assert issued["number"] == "INV-2026-0001" and issued["reference"] == order["order_number"]
    assert call(h, action="CANCEL_QUOTE", quote_id=q["quote_id"]).reason == "WRONG_STATE"


def test_decline_and_cancel_keep_the_reason(h):
    cust = call(h, action="SAVE_CUSTOMER", name="No Email Co").fields["customer_id"]
    mk = lambda: call(h, action="SAVE_QUOTE", customer_id=cust, lines=[{"description": "Buffet", "qty": 50, "unit_price": "20"}], **EVENT).fields["quote_id"]  # noqa: E731
    a, b = mk(), mk()
    assert call(h, action="SEND_QUOTE", quote_id=a, send=True).reason == "NO_EMAIL"
    assert call(h, action="DECLINE_QUOTE", quote_id=a, reason="Too expensive").fields["quote"]["close_reason"] == "Too expensive"
    call(h, action="ACCEPT_QUOTE", quote_id=b)
    assert call(h, action="CANCEL_QUOTE", quote_id=b, reason="Event called off").fields["quote"]["state"] == "cancelled"
    view = call(h, action="QUOTES").fields
    assert view["stages"]["declined"]["count"] == 1 and view["stages"]["cancelled"]["total"] == 100000 and view["win_rate"] == 0
