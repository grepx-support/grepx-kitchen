# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""My work (the staff phone screen): my published shifts, clocking with my PIN, hours, finalised payslips with the PDF,
leave balance and asking for leave - only my own."""
from datetime import date, timedelta

from kitchen_stack import env, ok, open_business  # noqa: F401


def test_my_work(env):
    stack, api = env
    owner = open_business(api, "My Kitchen", "owner@mywork.sg")["owner"]
    assert api.get("/api/v1/my", headers=owner).status_code == 404          # not on the team yet
    ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Store", "kind": "warehouse"}))
    k1 = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Kitchen", "kind": "kitchen"}))["location_id"]
    me = ok(api.post("/api/v1/team", headers=owner, json={"name": "Olive Owner", "email": "owner@mywork.sg", "position": "Chef", "home_site": k1,
                                                         "pay": {"basis": "monthly", "rate": 3000}}))["employee_id"]
    day = (date.today() + timedelta(days=2)).isoformat()
    ok(api.post("/api/v1/roster/shifts", headers=owner, json={"site_id": k1, "employee_id": me, "date": day, "start": "08:00", "end": "16:00"}))
    stack.settle()
    assert ok(api.get("/api/v1/my", headers=owner))["shifts"] == []                # not published yet
    ok(api.post("/api/v1/roster/publish", headers=owner, json={"site_id": k1, "week": day}))
    ok(api.post(f"/api/v1/team/{me}/pin", headers=owner, json={"pin": "1357"}))
    assert ok(api.post("/api/v1/my/clock", headers=owner, json={"pin": "1357", "site_id": k1}))["clocked"] == "in"
    month = date.today().isoformat()[:7]
    ok(api.post("/api/v1/payroll/run", headers=owner, json={"month": month}))
    stack.settle()
    assert ok(api.get("/api/v1/my", headers=owner))["payslips"] == []              # not final yet
    ok(api.post("/api/v1/payroll/finalise", headers=owner, json={"month": month}))
    stack.settle()
    mine = ok(api.get("/api/v1/my", headers=owner))
    assert mine["employee"]["name"] == "Olive Owner" and mine["shifts"][0]["site"] == "Kitchen" and mine["clocked_in"] is True
    assert mine["payslips"][0]["month"] == month and mine["balances"]
    assert api.get(f"/api/v1/my/payslips/{month}/pdf", headers=owner).content[:4] == b"%PDF"
    leave = ok(api.post("/api/v1/my/leave", headers=owner, json={"type_id": "annual", "first": "2026-12-28", "last": "2026-12-29"}))
    assert leave["state"] == "pending"
