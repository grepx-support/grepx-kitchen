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


def test_reorder_locations_of_own_business_only(h):
    for t in ("hft", "cafe"):
        call(h, action="CREATE", tenant_id=t, name=f"{t} Co", currency="AUD", timezone="Australia/Sydney")
    ids = [call(h, action="SAVE_LOCATION", tenant_id="hft", name=n, kind=k).fields["location"]["location_id"]
           for n, k in (("Central", "warehouse"), ("Shop", "store"))]
    assert call(h, action="REORDER_LOCATIONS", tenant_id="hft", ids=[ids[1], ids[0]]).ok
    rows = {r["_key"]: r for r in h.rows("locations")}
    assert (rows[ids[1]]["sort"], rows[ids[0]]["sort"]) == (0, 1) and rows[ids[0]]["kind"] == "warehouse"
    assert call(h, action="REORDER_LOCATIONS", tenant_id="cafe", ids=ids).reason == "INVALID_LIST"


def test_invoicing_details_are_kept_and_checked():
    from domain.rules import clean_billing
    got = clean_billing({"legal_name": " Demo Taco Pte Ltd ", "tax_label": "GST", "tax_rate": "9", "payment_note": "PayNow UEN 123"}, {"address": "1 Road"})
    assert got == {"address": "1 Road", "legal_name": "Demo Taco Pte Ltd", "tax_label": "GST", "tax_rate": 9, "payment_note": "PayNow UEN 123"}
    for bad in ({"tax_rate": "x"}, {"tax_rate": 80}):
        with pytest.raises(ValueError, match="INVALID_SETTING"):
            clean_billing(bad, {})


def test_close_and_reopen_keeps_the_business(h):
    call(h, action="CREATE", tenant_id="hft", name="HFT", currency="AUD", timezone="Australia/Sydney")
    closed = call(h, action="SET_CLOSED", tenant_id="hft", closed=True, actor_id="ops").fields["business"]
    assert closed["closed"] is True and closed["closed_by"] == "ops" and closed["name"] == "HFT" and closed["closed_at"]
    opened = call(h, action="SET_CLOSED", tenant_id="hft", closed=False).fields["business"]
    assert opened["closed"] is False and opened["currency"] == "AUD"
    assert call(h, action="SET_CLOSED", tenant_id="nope", closed=True).reason == "UNKNOWN_BUSINESS"
