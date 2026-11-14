# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Monthly costs through the kitchen API: cost lines per place, a shared cost, a month copied, the page and the Costs
summary line by line."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_monthly_costs_page(env):
    stack, api = env
    owner = open_business(api, "Cost Lines Co", "owner@costlines.sg")["owner"]
    ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Store", "kind": "warehouse"}))
    a = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Outlet A", "kind": "store"}))["location_id"]
    b = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Outlet B", "kind": "store"}))["location_id"]
    ok(api.post("/api/v1/setup/overheads", headers=owner, json={"location_id": a, "month": "2026-10", "lines": [
        {"category": "Salaries and wages", "amount": 5000}, {"category": "Rent", "amount": 3000}, {"category": "Delivery-app commission", "amount": 800, "note": "Grab + Foodpanda"},
        {"category": "Security guard", "group": "other", "amount": 400}]}))
    shared = ok(api.post("/api/v1/setup/overheads/share", headers=owner, json={"month": "2026-10", "category": "Accountant", "amount": 1000,
                                                                              "rule": "equal", "location_ids": [a, b]}))
    assert [s["amount"] for s in shared["shares"]] == [500, 500]
    assert ok(api.post("/api/v1/setup/overheads/copy", headers=owner, json={"from_month": "2026-10", "to_month": "2026-11"}))["copied"] == 2
    page = ok(api.get("/api/v1/setup/overheads?month=2026-11&months=2", headers=owner))
    cells = {(c["location_id"], c["month"]): c for c in page["cells"]}
    assert cells[(a, "2026-11")]["total"] == 9700 and cells[(b, "2026-10")]["shared"] == 500
    assert "Security guard" in {c["category"] for c in page["categories"]} and page["per_month"][0]["other"] == 2200
    lines = ok(api.get(f"/api/v1/costs/month?month=2026-10&location_id={a}", headers=owner))["cost_lines"]
    assert lines and lines[0]["category"] == "Salaries and wages"
    assert api.post("/api/v1/setup/overheads/share", headers=owner, json={"month": "2026-10", "amount": 5}).status_code == 409   # no cost named
