# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The demo's funds (demo/funds.py with india.py and data.py) load through the API and give the Funds page something
to show: real costs linked to the places, a promise overdue, money in another currency, suggestions and a forecast."""
import sys
from datetime import date
from pathlib import Path

import pytest

from kitchen_stack import env, ok, open_business  # noqa: F401

DEMO = Path(__file__).resolve().parents[3] / "demo"
sys.path.insert(0, str(DEMO))
import data, funds, india, setup  # noqa: E402,E401


class Site:
    """demo/api.Site over the test client: the same post / put, as the owner."""
    def __init__(self, api, owner):
        self.api, self.owner = api, owner

    def post(self, path, body, who):
        return ok(self.api.post(f"/api/v1{path}", headers=self.owner, json=body))

    def put(self, path, body, who):
        return ok(self.api.put(f"/api/v1{path}", headers=self.owner, json=body))


@pytest.mark.parametrize("d", [india, data], ids=["india", "taco"])
def test_demo_funds_fill_the_funds_page(env, d):
    stack, api = env
    owner = open_business(api, d.BUSINESS["name"] + " funds", f"funds@{d.BUSINESS['currency'].lower()}.test", d.BUSINESS["currency"], d.BUSINESS["timezone"])["owner"]
    site = Site(api, owner)
    places = {key: site.post("/setup/locations", {"name": name, "kind": kind}, "owner")["location_id"] for key, name, kind, *_ in d.PLACES}
    setup.monthly_costs(site, d, {"place": places})                      # the demo's six months of cost lines and a shared fee
    page = ok(api.get(f"/api/v1/setup/overheads?month={date.today().isoformat()[:7]}", headers=owner))
    assert len(page["by_category"]) > 10 and "Accountant" in {c["category"] for c in page["by_category"]}
    funds.run(site, d, {}, lambda *_: None)
    o = ok(api.get("/api/v1/funds", headers=owner))
    p = o["position"]
    assert len(o["funds"]) == len(d.FUNDS) and o["in_base"]["unconverted"] == []
    assert {u["purpose"] for u in p["linked"] if u["spent"]} >= {name for key, name, *_ in d.PLACES if key in d.OVERHEADS} & {u["purpose"] for u in p["linked"]}
    assert any(u["over"] for u in p["linked"]) and any(x["overdue"] for x in p["promises"]) and any(not x["overdue"] for x in p["promises"])
    assert {"CHASE_PROMISE", "USE_OVERSPENT"} <= {t["code"] for t in p["suggestions"]}
    assert p["forecast"]["burn"] > 0 and all(b["balances"] for b in o["balance_sheet"].values())
