# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""costing-service monthly costs as lines: categories in three groups, shared costs split over places, a month
started from the month before, the page grid with month-on-month change, and the old three-amount form still working."""
import pytest

from domain import clean_lines, grid, split, totals
from test_costing_service import h  # noqa: F401  (h is the shared fixture)

T = "costing_requests"


def call(h, **f):
    return h.call(T, "costing-service", {"tenant_id": "hft", **f})


def test_lines_split_and_grid():
    lines = clean_lines([{"category": "Electricity", "amount": "120.5"}, {"category": "Electricity", "amount": 10}, {"category": "Rent", "amount": 3000},
                         {"category": "Chef", "group": "labour", "amount": 4000}, {"category": "Empty", "amount": ""}])
    assert totals(lines) == {"labour": 4000, "rent": 3000, "other": 130.5} and len(lines) == 3
    for bad in ([{"category": "X", "amount": -1}], [{"category": "X", "group": "food", "amount": 1}]):
        with pytest.raises(ValueError):
            clean_lines(bad)
    assert split(100, {"a": 1, "b": 1, "c": 1}) == {"a": 33.33, "b": 33.33, "c": 33.34}
    assert split(1000, {"a": 300, "b": 100, "c": 0}) == {"a": 750.0, "b": 250.0}
    g = grid([{"location_id": "s", "month": "2026-09", "labour": 100, "rent": 0, "other": 0},
              {"location_id": "s", "month": "2026-10", "lines": [{"category": "Rent", "group": "rent", "amount": 150}]}], {"s": "Shop"}, ["2026-09", "2026-10"])
    assert [c["total"] for c in g] == [100, 150] and g[1]["change_pct"] == 50.0 and g[0]["lines"][0]["category"] == "Salaries and wages"


def test_costs_page_share_and_copy(h):
    h.seed("locations", "s2", {"tenant_id": "hft", "name": "Kitchen", "kind": "kitchen", "active": True})
    assert call(h, action="SET_OVERHEAD", location_id="s1", month="2026-10", lines=[{"category": "Rent", "amount": -5}]).reason == "INVALID_AMOUNT"
    own = call(h, action="SET_OVERHEAD", location_id="s1", month="2026-10",
               lines=[{"category": "Salaries and wages", "amount": 3100}, {"category": "Electricity", "amount": 310}]).fields["overhead"]
    assert (own["labour"], own["rent"], own["other"]) == (3100, 0, 310)
    shared = call(h, action="SHARE_OVERHEAD", month="2026-10", category="Accountant", group="other", amount=1000, rule="sales", location_ids=["s1", "s2"]).fields
    assert {s["location_id"]: s["amount"] for s in shared["shares"]} == {"s1": 1000.0, "s2": 0}         # only the truck sold in October
    equal = call(h, action="SHARE_OVERHEAD", month="2026-10", category="Accountant", group="other", amount=900, rule="equal", location_ids=["s1", "s2"]).fields
    assert [s["amount"] for s in equal["shares"]] == [450, 450]                                          # the same category again: replaced
    again = call(h, action="SET_OVERHEAD", location_id="s1", month="2026-10", lines=[{"category": "Salaries and wages", "amount": 3200}]).fields["overhead"]
    assert {l["category"] for l in again["lines"]} == {"Salaries and wages", "Accountant"} and again["other"] == 450   # shares kept
    day = h.rows("cost_days")
    assert day and all(round(d["labour"], 2) == round(3200 / 31 * d["period_days"], 2) for d in day if d["date"].startswith("2026-10"))
    assert call(h, action="COPY_OVERHEADS", from_month="2026-10", to_month="2026-11").fields["copied"] == 2
    assert call(h, action="COPY_OVERHEADS", from_month="2026-10", to_month="2026-11").fields["copied"] == 0     # already there
    page = call(h, action="OVERHEADS", month="2026-11", months=2).fields
    assert page["months"] == ["2026-10", "2026-11"] and page["per_month"][1]["total"] == 3200 + 450 + 450
    assert page["by_category"][0] == {"category": "Salaries and wages", "group": "labour", "amount": 3200}
    assert "Delivery-app commission" in {c["category"] for c in page["categories"]} and "Accountant" in {c["category"] for c in page["categories"]}
    assert call(h, action="SET_OVERHEAD", location_id="s1", month="2026-12", labour=1, rent=2, other=3).fields["overhead"]["rent"] == 2  # the old form
    summary = call(h, action="SUMMARY", month="2026-10", location_id="s1").fields["summary"]
    assert {c["category"] for c in summary["cost_lines"]} == {"Salaries and wages", "Accountant"}
