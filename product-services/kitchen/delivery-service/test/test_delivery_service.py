# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""delivery-service: runs of warehouse-out trips, arrival estimates, proof of delivery, failed stops."""
from datetime import datetime
from pathlib import Path

import pytest
from grepx_config import load_config
from grepx_testkit.harness import ServiceHarness

from domain import check_signature, clean_run, eta
from routes import handle

cfg = load_config(Path(__file__).resolve().parents[1] / "config")
T = "delivery_requests"


def test_arrival_estimates_count_drive_and_unload_time():
    run = {**clean_run({"date": "2026-11-10", "start_time": "07:30", "drive_minutes": 20, "service_minutes": 10}), "state": "planned"}
    stops = [{"stop_id": "a", "state": "delivered"}, {"stop_id": "b", "state": "pending"}, {"stop_id": "c", "state": "pending"}]
    assert [s.get("eta") for s in eta(run, stops)] == [None, "07:50", "08:20"]
    moving = eta({**run, "state": "on_road"}, stops, datetime(2026, 11, 10, 9, 0))
    assert [s.get("eta") for s in moving] == [None, "09:20", "09:50"]
    with pytest.raises(ValueError, match="INVALID_TIME"):
        clean_run({"date": "2026-11-10", "start_time": "7am"})
    with pytest.raises(ValueError, match="SIGNATURE_TOO_LARGE"):
        check_signature("data:image/png;base64," + "A" * 70000)
    with pytest.raises(ValueError):
        check_signature("javascript:alert(1)")


@pytest.fixture()
def h():
    harness = ServiceHarness().add(cfg, T, handle, cfg.live_criteria)
    for tenant in ("hft", "cafe"):
        harness.seed("businesses", tenant, {"business_id": tenant, "tenant_id": tenant})
    harness.seed("locations", "s1", {"tenant_id": "hft", "name": "Bondi", "address": "Bondi Beach"})
    harness.seed("locations", "s2", {"tenant_id": "hft", "name": "Parra", "address": "Parramatta"})
    for key, to in (("d1", "s1"), ("d2", "s2"), ("d3", "s1")):
        harness.seed("deliveries", key, {"tenant_id": "hft", "state": "sent", "to_location_id": to, "lines": 2})
    harness.seed("deliveries", "old", {"tenant_id": "hft", "state": "delivered", "to_location_id": "s1"})
    return harness


def call(h, **fields):
    return h.call(T, "delivery-service", {"actor_id": "u9", "actor_name": "Dan", **fields})


def test_a_run_from_plan_to_proof_of_delivery(h):
    plan = call(h, action="PLAN_RUN", tenant_id="hft", date="2026-11-10", start_time="08:00", driver_name="Dan", delivery_ids=["d2", "d1"])
    run = plan.fields["run"]
    assert plan.ok and [s["name"] for s in run["stops"]] == ["Parra", "Bondi"] and run["stops"][0]["eta"] == "08:25"
    rid = run["run_id"]
    assert call(h, action="PLAN_RUN", tenant_id="hft", date="2026-11-10", delivery_ids=["d1"]).reason == "ON_ANOTHER_RUN"
    assert call(h, action="PLAN_RUN", tenant_id="hft", date="2026-11-10", delivery_ids=["old"]).reason == "ALREADY_DELIVERED"
    assert call(h, action="PLAN_RUN", tenant_id="cafe", date="2026-11-10", delivery_ids=["d3"]).reason == "UNKNOWN_DELIVERY"
    assert call(h, action="SET_STOPS", tenant_id="hft", run_id=rid, delivery_ids=["d1", "d3", "d2"]).ok          # dragged into a new order
    assert call(h, action="ARRIVE", tenant_id="hft", run_id=rid, stop_id="d1").reason == "WRONG_STATE"           # not on the road yet
    assert call(h, action="START_RUN", tenant_id="hft", run_id=rid).ok
    assert call(h, action="DELIVER", tenant_id="hft", run_id=rid, stop_id="d1", receiver="").reason == "RECEIVER_REQUIRED"
    assert call(h, action="ARRIVE", tenant_id="hft", run_id=rid, stop_id="d1").ok
    assert call(h, action="DELIVER", tenant_id="hft", run_id=rid, stop_id="d1", receiver="Tia", driver_signature="http://x").reason == "SIGNATURE_TOO_LARGE"
    done = call(h, action="DELIVER", tenant_id="hft", run_id=rid, stop_id="d1", receiver="Tia", signature="data:image/png;base64,AAA",
                driver_signature="data:image/png;base64,BBB")
    assert done.fields["run"]["stops"][0]["driver_signature"].endswith("BBB")
    assert done.ok and done.fields["run"]["stops"][0]["receiver"] == "Tia"
    pod = h.rows("stock_requests")[0]
    assert (pod["action"], pod["delivery_id"]) == ("DELIVERED", "d1")
    assert call(h, action="FAIL_STOP", tenant_id="hft", run_id=rid, stop_id="d3", reason="x").reason == "REASON_REQUIRED"
    assert call(h, action="FAIL_STOP", tenant_id="hft", run_id=rid, stop_id="d3", reason="Shop closed").ok
    last = call(h, action="DELIVER", tenant_id="hft", run_id=rid, stop_id="d2", receiver="Sam")
    assert last.fields["run"]["state"] == "done"
    again = call(h, action="PLAN_RUN", tenant_id="hft", date="2026-11-11", delivery_ids=["d3"])          # the failed trip goes out again
    assert again.ok
