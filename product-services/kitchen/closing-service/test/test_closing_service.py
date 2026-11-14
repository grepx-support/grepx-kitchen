# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""closing-service: one short closing per location and day; the count goes to stock-service."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_closing
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "closing_requests"


def test_rules():
    today = date(2026, 11, 9)
    c = clean_closing({"staff_name": "Ana", "counts": [{"item_id": "b", "qty": "4"}, {"item_id": "c", "qty": ""}],
                       "sales": {"Sales": "812.5", "Other sales": 40}}, today, ["Sales", "Other sales"])
    assert c["counts"] == [{"item_id": "b", "qty": 4}] and c["total_sales"] == 852.5 and c["date"] == "2026-11-09"
    for bad, reason in [({"staff_name": ""}, "STAFF_NAME_REQUIRED"), ({"staff_name": "Ana", "date": "2026-11-10"}, "INVALID_DATE"),
                        ({"staff_name": "Ana", "sales": {"Tips": 5}}, "UNKNOWN_SALES_TYPE"),
                        ({"staff_name": "Ana", "counts": [{"item_id": "b", "qty": -1}]}, "INVALID_QUANTITY")]:
        with pytest.raises(ValueError, match=reason):
            clean_closing(bad, today, ["Sales", "Other sales"])


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    harness.seed("businesses", "hft", {"business_id": "hft", "tenant_id": "hft", "timezone": "UTC", "settings": {"sales_types": ["Sales"]}})
    harness.seed("locations", "s1", {"tenant_id": "hft", "name": "Truck", "kind": "truck", "active": True})
    harness.seed("items", "birria", {"tenant_id": "hft", "kind": "finished", "cost": 6})
    harness.seed("stock_levels", "s1:birria", {"tenant_id": "hft", "location_id": "s1", "item_id": "birria", "qty": 30})
    return harness


def test_submit_once_and_count_goes_to_stock(h):
    fields = {"action": "SUBMIT", "tenant_id": "hft", "location_id": "s1", "actor_id": "u1", "staff_name": "Ana",
              "issues": "Fridge door loose", "counts": [{"item_id": "birria", "qty": 12}], "sales": {"Sales": 640}}
    v = h.call(T, "closing-service", fields)
    assert v.ok and v.fields["closing"]["counts"][0]["expected"] == 30 and v.fields["closing"]["total_sales"] == 640
    sent = h.rows("stock_requests")
    assert len(sent) == 1 and sent[0]["action"] == "COUNT" and sent[0]["lines"] == [{"item_id": "birria", "qty": 12}]
    assert sent[0]["ref"] == v.fields["closing"]["closing_id"] and sent[0]["actor_name"] == "Ana"
    assert h.call(T, "closing-service", fields).reason == "ALREADY_SUBMITTED"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    assert h.call(T, "closing-service", {**fields, "date": yesterday, "location_id": "elsewhere"}).reason == "UNKNOWN_LOCATION"
    assert h.call(T, "closing-service", {**fields, "date": yesterday, "tenant_id": "x"}).reason == "UNKNOWN_BUSINESS"
