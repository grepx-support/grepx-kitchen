# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""business-service: businesses are separate tenants; locations keep a holding place."""
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import clean_business, clean_location
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "business_requests"


@pytest.fixture()
def h():
    return ServiceHarness().add(cfg, T, handle, cfg.live_criteria)


def call(h, **fields):
    return h.call(T, "business-service", fields)


def test_rules():
    b = clean_business({"name": "Halal Fusion Taco", "currency": "aud", "timezone": "Australia/Sydney"})
    assert b["currency"] == "AUD" and all(b["modules"].values()) and b["settings"]["target_weeks"] == 2
    with pytest.raises(ValueError, match="INVALID_TIMEZONE"):
        clean_business({"name": "X Co", "currency": "AUD", "timezone": "Mars/Base"})
    with pytest.raises(ValueError, match="INVALID_SETTING"):
        clean_business({"settings": {"target_weeks": 5}}, b)
    with pytest.raises(ValueError, match="INVALID_SETTING"):
        clean_business({"settings": {"cogs_min": 40, "cogs_max": 30}}, b)
    w = clean_location({"name": "Central", "kind": "warehouse"})
    assert w["holding"] and not w["makes_goods"]
    k = clean_location({"name": "Kitchen + freezer", "kind": "kitchen", "holding": True})   # D2 / BUS-04
    assert k["holding"] and k["makes_goods"]
    with pytest.raises(ValueError, match="INVALID_SETTING"):
        clean_location({"name": "Truck", "kind": "truck", "count_every_days": 2})


def test_business_lifecycle_and_separation(h):
    assert call(h, action="CREATE", tenant_id="hft", name="HFT", currency="AUD", timezone="Australia/Sydney").ok
    assert call(h, action="CREATE", tenant_id="hft", name="HFT", currency="AUD", timezone="Australia/Sydney").reason == "BUSINESS_EXISTS"
    assert call(h, action="CREATE", name="No tenant", currency="AUD", timezone="UTC").reason == "MISSING_TENANT"
    v = call(h, action="UPDATE", tenant_id="hft", modules={"kitchen": False}, settings={"cogs_max": 33})
    assert v.ok and v.fields["business"]["modules"]["kitchen"] is False and v.fields["business"]["settings"]["cogs_max"] == 33
    assert call(h, action="UPDATE", tenant_id="other", name="X").reason == "UNKNOWN_BUSINESS"


def test_locations_need_a_holding_place_and_stay_in_their_business(h):
    call(h, action="CREATE", tenant_id="hft", name="HFT", currency="AUD", timezone="Australia/Sydney")
    call(h, action="CREATE", tenant_id="cafe", name="Cafe", currency="SGD", timezone="Asia/Singapore")
    w = call(h, action="SAVE_LOCATION", tenant_id="hft", name="Warehouse", kind="warehouse")
    assert w.ok
    wid = w.fields["location"]["location_id"]
    s = call(h, action="SAVE_LOCATION", tenant_id="hft", name="Store 1", kind="store", days_of_cover=2)
    assert s.ok and s.fields["location"]["days_of_cover"] == 2
    assert call(h, action="SAVE_LOCATION", tenant_id="hft", location_id=wid, holding=False).reason == "NO_HOLDING_LOCATION"
    assert call(h, action="SAVE_LOCATION", tenant_id="cafe", location_id=wid, name="Mine now").reason == "UNKNOWN_LOCATION"
    assert call(h, action="SAVE_LOCATION", tenant_id="hft", name="Boat", kind="boat").reason == "INVALID_KIND"
    assert len(h.rows("locations", tenant_id="hft")) == 2
