# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""billing-service: customers, draft -> issued invoices with gapless numbers, payments, credit notes, void, ageing."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import ageing, clean_customer, clean_lines, next_number, status
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "billing_requests"


# ---------------- rules ----------------
def test_customer_and_lines_are_checked():
    assert clean_customer({"name": " Cafe Uno ", "email": "A@B.CO", "terms_days": "14"})["terms_days"] == 14
    for bad, reason in (({"name": ""}, "CUSTOMER_NAME_REQUIRED"), ({"name": "x", "email": "nope"}, "INVALID_EMAIL"),
                        ({"name": "x", "terms_days": 400}, "INVALID_TERMS")):
        with pytest.raises(ValueError, match=reason):
            clean_customer(bad)
    lines = clean_lines([{"item_id": "taco", "qty": "3", "unit_price": "4.50"}, {"description": "", "qty": ""},
                         {"description": "Delivery", "qty": 1, "unit_price": "12", "discount": 50}], {"taco": {"name": "Tacos", "unit": "box"}})
    assert [(l["description"], l["amount"]) for l in lines] == [("Tacos", 1350), ("Delivery", 600)]
    with pytest.raises(ValueError, match="UNKNOWN_ITEM"):
        clean_lines([{"item_id": "ghost", "qty": 1, "unit_price": 1}], {})
    with pytest.raises(ValueError, match="NO_LINES"):
        clean_lines([], {})


def test_numbers_are_gapless_per_kind_and_year():
    assert next_number("invoice", 2026, ["INV-2026-0001", "INV-2026-0007", "INV-2025-0099", "CN-2026-0003"]) == "INV-2026-0008"
    assert next_number("credit", 2027, ["CN-2026-0003"]) == "CN-2027-0001"


def test_status_and_ageing():
    inv = {"state": "issued", "kind": "invoice", "total": 1000, "paid": 0, "due": "2026-10-01"}
    assert status(inv, "2026-09-30") == "open" and status(inv, "2026-10-02") == "overdue"
    assert status({**inv, "paid": 100}, "2026-09-30") == "part paid"
    got = ageing([inv, {**inv, "due": "2026-11-30"}, {**inv, "state": "paid"}], "2026-11-20")
    assert (got["current"], got["31-60"]) == (1000, 1000)


# ---------------- service ----------------
@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "name": "HFT", "currency": "SGD"})
    harness.seed("businesses", "cafe", {"business_id": "cafe", "tenant_id": "cafe", "timezone": "UTC"})
    harness.seed("items", "taco", {"tenant_id": "hft", "name": "Tacos", "unit": "box", "kind": "finished"})
    return harness


def call(h, **fields):
    return h.call(T, "billing-service", {"actor_id": "u1", "actor_name": "Olivia", "tenant_id": "hft", **fields})


def draft(h, **extra):
    cust = call(h, action="SAVE_CUSTOMER", name="Cafe Uno", email="ap@uno.test", terms_days=14).fields["customer_id"]
    inv = call(h, action="SAVE_INVOICE", customer_id=cust, tax_rate=9, lines=[{"item_id": "taco", "qty": 10, "unit_price": "4.50"}], **extra)
    assert inv.ok, inv.reason
    return inv.fields["invoice_id"]


def test_invoice_lifecycle_issue_pay_in_parts(h):
    key = draft(h)
    inv = h.rows("invoices")[0]
    assert (inv["subtotal"], inv["tax"], inv["total"], inv["state"]) == (4500, 405, 4905, "draft")
    issued = call(h, action="ISSUE_INVOICE", invoice_id=key, issued="2026-11-13", send=True).fields["invoice"]
    assert (issued["number"], issued["due"]) == ("INV-2026-0001", "2026-11-27")
    assert h.rows("notifications")[0]["template"] == "customer_invoice"
    assert call(h, action="SAVE_INVOICE", invoice_id=key, customer_id=issued["customer_id"], lines=[{"description": "x", "qty": 1, "unit_price": 1}]).reason == "NOT_A_DRAFT"
    assert call(h, action="RECORD_PAYMENT", invoice_id=key, amount="50", date="2026-11-14").reason == "MORE_THAN_DUE"
    part = call(h, action="RECORD_PAYMENT", invoice_id=key, amount="20.00", date="2026-11-14", method="paynow").fields["invoice"]
    assert (part["paid"], part["state"]) == (2000, "issued")
    assert call(h, action="VOID_INVOICE", invoice_id=key).reason == "HAS_PAYMENTS"
    paid = call(h, action="RECORD_PAYMENT", invoice_id=key, amount="29.05", date="2026-11-15").fields["invoice"]
    assert (paid["paid"], paid["state"], len(paid["payments"])) == (4905, "paid", 2)
    second = draft(h)
    assert call(h, action="ISSUE_INVOICE", invoice_id=second, issued="2026-12-01").fields["invoice"]["number"] == "INV-2026-0002"


def test_credit_note_reverses_and_void_keeps_the_number(h):
    key = draft(h)
    call(h, action="ISSUE_INVOICE", invoice_id=key, issued="2026-11-13")
    note = call(h, action="CREDIT_NOTE", invoice_id=key, reason="Wrong delivery")
    assert note.ok, note.reason
    cn = note.fields["credit_note"]
    assert (cn["number"][:3], cn["total"], cn["corrects_number"]) == ("CN-", 4905, "INV-2026-0001")
    assert next(r for r in h.rows("invoices") if r["_key"] == key)["state"] == "paid"
    other = draft(h)
    assert call(h, action="VOID_INVOICE", invoice_id=other, reason="duplicate").fields["invoice"]["state"] == "void"


def test_another_business_cannot_touch_these(h):
    key = draft(h)
    assert call(h, action="ISSUE_INVOICE", invoice_id=key, tenant_id="cafe").reason == "UNKNOWN_INVOICE"
    assert call(h, action="SAVE_INVOICE", tenant_id="cafe", customer_id="x", lines=[]).reason == "UNKNOWN_CUSTOMER"


def test_summary_shows_status_ageing_and_month(h):
    key = draft(h)
    call(h, action="ISSUE_INVOICE", invoice_id=key, issued="2020-01-01")
    s = call(h, action="SUMMARY").fields
    assert s["invoices"][0]["status"] == "overdue" and s["overdue"] == 4905 and s["ageing"]["90+"] == 4905


def test_issuing_takes_the_goods_out_of_stock_where_they_are_sent_from(h):
    h.seed("locations", "wh", {"tenant_id": "hft", "name": "Warehouse", "kind": "warehouse"})
    cust = call(h, action="SAVE_CUSTOMER", name="Cafe Uno").fields["customer_id"]
    assert call(h, action="SAVE_INVOICE", customer_id=cust, location_id="nowhere", lines=[{"item_id": "taco", "qty": 1, "unit_price": 1}]).reason == "UNKNOWN_LOCATION"
    key = call(h, action="SAVE_INVOICE", customer_id=cust, location_id="wh",
               lines=[{"item_id": "taco", "qty": "2.5", "unit_price": "4"}, {"description": "Delivery", "qty": 1, "unit_price": 5}]).fields["invoice_id"]
    call(h, action="ISSUE_INVOICE", invoice_id=key, issued="2026-11-13")
    ask = h.rows("stock_requests")[0]
    assert (ask["action"], ask["location_id"], ask["lines"], ask["invoice_number"]) == ("SELL", "wh", [{"item_id": "taco", "qty": 2.5}], "INV-2026-0001")


def test_statement_runs_the_balance_and_reminders_go_once_per_stage(h):
    from domain import reminder_stage, statement
    key = draft(h)
    call(h, action="ISSUE_INVOICE", invoice_id=key, issued="2026-10-01")
    call(h, action="RECORD_PAYMENT", invoice_id=key, amount="9.05", date="2026-10-20")
    cust = h.rows("invoices")[0]["customer_id"]
    s = call(h, action="STATEMENT", customer_id=cust).fields
    assert [(l["what"], l["amount"], l["balance"]) for l in s["lines"]] == [("invoice", 4905, 4905), ("payment", -905, 4000)]
    assert s["owed"] == 4000 and s["open"][0]["number"] == "INV-2026-0001"
    inv = next(r for r in h.rows("invoices") if r["_key"] == key)           # due 2026-10-15
    assert reminder_stage(inv, "2026-10-15") is None and reminder_stage(inv, "2026-10-23") == 7
    assert reminder_stage({**inv, "reminders": [{"stage": 7}]}, "2026-10-23") is None
    sent = call(h, action="SEND_REMINDER", invoice_id=key)
    assert sent.ok and h.rows("notifications")[-1]["template"] == "payment_reminder" and sent.fields["invoice"]["reminders"][0]["stage"] == "manual"
    assert statement([], "x", "2026-10-01")["owed"] == 0


def test_the_daily_job_reminds_only_businesses_that_asked(h):
    from grepx_service import Reader  # noqa: F401
    from jobs import handle_tick
    from nexus_api import NexusApplication, Row
    from nexus_testkit import MemoryClient
    key = draft(h)
    call(h, action="ISSUE_INVOICE", invoice_id=key, issued="2020-01-01")
    app = NexusApplication(MemoryClient(h.engine), "x")
    assert handle_tick(app, Row("t1", {"job": "billing-reminders", "status": "NEW"}), cfg) == 0          # reminders off
    h.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "name": "HFT", "currency": "SGD",
                                 "billing": {"auto_reminders": True}})
    assert handle_tick(app, Row("t2", {"job": "billing-reminders", "status": "NEW"}), cfg) == 1
    assert handle_tick(app, Row("t3", {"job": "billing-reminders", "status": "NEW"}), cfg) == 0          # once per stage


def test_months_count_issued_sales_less_credits_and_payments():
    from domain import monthly
    rows = [{"state": "issued", "kind": "invoice", "issued": "2026-03-04", "taxable": 1000, "tax": 90, "total": 1090, "payments": [{"date": "2026-04-01", "amount": 500}]},
            {"state": "paid", "kind": "credit", "issued": "2026-03-20", "taxable": 200, "tax": 18, "total": 218},
            {"state": "draft", "kind": "invoice", "issued": "2026-03-05", "taxable": 999, "tax": 0, "total": 999},
            {"state": "void", "kind": "invoice", "issued": "2026-03-06", "taxable": 999, "tax": 0, "total": 999},
            {"state": "issued", "kind": "invoice", "issued": "2025-12-31", "taxable": 5, "tax": 0, "total": 5}]
    months = monthly(rows, 2026)
    assert len(months) == 12 and months[0]["month"] == "2026-01"
    assert {k: months[2][k] for k in ("sales", "tax", "total", "invoices", "credits")} == {"sales": 800, "tax": 72, "total": 872, "invoices": 1, "credits": 1}
    assert months[3]["received"] == 500 and sum(m["sales"] for m in months) == 800


def test_monthly_action_defaults_to_this_year(h):
    got = call(h, action="MONTHLY", year="nonsense").fields
    assert len(got["months"]) == 12 and str(got["year"]) == got["months"][0]["month"][:4]
    assert str(call(h, action="MONTHLY", year=2024).fields["year"]) == "2024"


def test_margins_per_product_and_customer():
    from domain import margins, period
    items = {"taco": {"name": "Tacos", "unit": "box", "cost": "3.00"}, "salsa": {"name": "Salsa", "unit": "jar", "cost": "0"}}
    line = lambda item, qty, amount: {"item_id": item, "qty": qty, "amount": amount}
    rows = [{"invoice_id": "i1", "state": "issued", "kind": "invoice", "issued": "2026-11-02", "customer_id": "uno", "discount_rate": "10",
             "lines": [line("taco", "10", 5000), line("salsa", "2", 1000), line("", "1", 2000)]},
            {"invoice_id": "i2", "state": "paid", "kind": "invoice", "issued": "2026-11-05", "customer_id": "dos", "lines": [line("taco", "2.5", 500)]},
            {"invoice_id": "c1", "state": "paid", "kind": "credit", "issued": "2026-11-06", "customer_id": "uno", "lines": [line("taco", "1", 500)]},
            {"invoice_id": "i3", "state": "draft", "kind": "invoice", "issued": "2026-11-06", "customer_id": "uno", "lines": [line("taco", "99", 1)]},
            {"invoice_id": "i4", "state": "issued", "kind": "invoice", "issued": "2026-10-31", "customer_id": "uno", "lines": [line("taco", "99", 1)]}]
    got = margins(rows, items, {"uno": "Cafe Uno"}, "2026-11-01", "2026-11-30")
    taco = next(p for p in got["products"] if p["item_id"] == "taco")
    # 4500 (5000 less 10 %) + 500 - 500 credit; cost (10 + 2.5 - 1) x 300
    assert (taco["revenue"], taco["cost"], taco["profit"], taco["qty"], taco["invoices"], taco["customers"]) == (4500, 3450, 1050, "11.5", 3, 2)
    assert taco["margin"] == 23.3
    other = next(p for p in got["products"] if p["item_id"] == "")
    assert (other["revenue"], other["cost"]) == (1800, 0)
    assert got["no_cost"] == ["Salsa"] and got["below_cost"] == []
    uno = next(c for c in got["customers"] if c["customer_id"] == "uno")
    assert (uno["name"], uno["revenue"], uno["cost"], uno["invoices"]) == ("Cafe Uno", 4500 + 900 + 1800 - 500, 3000 - 300, 2)
    assert got["total"]["revenue"] == 4500 + 900 + 1800 and got["total"]["profit"] == got["total"]["revenue"] - 3450
    assert period("", "", "2026-11-13") == ("2026-11-01", "2026-11-13")
    # a made product with no cost of its own is costed from its recipe: 2 kg of 4.00 + 0.5 jar of 1.00 per 10 made
    items = {**items, "birria": {"name": "Birria", "unit": "box"}, "beef": {"name": "Beef", "cost": "4"}, "jar": {"name": "Jar", "cost": "1"}}
    recipes = {"birria": {"batch_output": "10", "ingredients": [{"item_id": "beef", "qty": "2"}, {"item_id": "jar", "qty": "0.5"}]}}
    sold = [{"invoice_id": "b", "state": "issued", "kind": "invoice", "issued": "2026-11-03", "customer_id": "uno", "lines": [line("birria", "4", 4000)]}]
    got = margins(sold, items, {}, "2026-11-01", "2026-11-30", recipes)
    assert (got["products"][0]["cost"], got["products"][0]["cost_from"], got["no_cost"]) == (340, "recipe", [])
    for bad in (("2026-11-05", "2026-11-01"), ("nope", "")):
        with pytest.raises(ValueError, match="INVALID_DATE"):
            period(*bad, "2026-11-13")


def test_margins_action(h):
    got = call(h, action="MARGINS").fields
    assert got["products"] == [] and got["total"]["revenue"] == 0
    assert call(h, action="MARGINS", **{"from": "2026-12-01", "to": "2026-01-01"}).reason == "INVALID_DATE"
