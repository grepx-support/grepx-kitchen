# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Funds round: a use named like a place shows that place's real costs; forecast, suggestions, balance-sheet detail,
money in another currency, reordering, and the investor statement as a PDF sent by email."""
import base64
from datetime import date, timedelta

from kitchen_stack import env, ok, open_business  # noqa: F401


def test_funds_linked_to_real_costs(env):
    stack, api = env
    owner = open_business(api, "Fund Kitchen", "owner@fund.sg")["owner"]
    ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Store", "kind": "warehouse"}))
    loc = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Orchard outlet", "kind": "store"}))["location_id"]
    month = (date.today().replace(day=1) - timedelta(days=1)).isoformat()[:7]        # last month: costs of a whole month
    ok(api.post("/api/v1/setup/overheads", headers=owner, json={"month": month, "location_id": loc, "labour": 4000, "rent": 3000, "other": 500}))
    fund = ok(api.post("/api/v1/funds", headers=owner, json={"name": "Partners", "kind": "equity"}))["fund_id"]
    loan = ok(api.post("/api/v1/funds", headers=owner, json={"name": "Bank loan", "kind": "loan", "rate_pct": 9}))["fund_id"]
    asha = ok(api.post("/api/v1/funds/parties", headers=owner, json={"name": "Asha", "email": "asha@inv.sg"}))["party_id"]
    rec = lambda f, **b: ok(api.post(f"/api/v1/funds/{f}/entries", headers=owner, json=b))  # noqa: E731
    paid = rec(fund, kind="receive", party_id=asha, amount=5000, currency="USD", rate="1.35", date=f"{month}-01")
    assert (paid["amount"], paid["original"]["currency"]) == (675000, "USD")
    rec(fund, kind="commit", party_id=asha, amount=20000, date=f"{month}-01", due=f"{month}-10")
    rec(fund, kind="allocate", amount=5000, purpose="Orchard outlet", date=f"{month}-02")
    o = ok(api.get("/api/v1/funds", headers=owner))
    use = o["position"]["linked"][0]
    assert use["purpose"] == "Orchard outlet" and use["spent"] == 750000 and use["over"]                 # 7,500 of costs vs 5,000 given
    assert {c["category"] for c in use["categories"]} == {"Labour", "Rent", "Other costs"}
    assert {"CHASE_PROMISE", "USE_OVERSPENT"} <= {t["code"] for t in o["position"]["suggestions"]}
    assert o["position"]["forecast"]["runway"]["expected"] is not None and o["balance_sheet"]["SGD"]["balances"]
    one = ok(api.get(f"/api/v1/funds/{fund}", headers=owner))
    assert one["linked"][0]["burn"] == 750000 and len(one["forecast"]["cases"]["worst"]["months"]) == 12
    ok(api.post("/api/v1/funds/order", headers=owner, json={"fund_ids": [loan, fund]}))
    assert [f["fund_id"] for f in ok(api.get("/api/v1/funds", headers=owner))["funds"]] == [loan, fund]
    pdf = api.get(f"/api/v1/funds/parties/{asha}/statement", headers=owner)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    ok(api.post(f"/api/v1/funds/parties/{asha}/statement/send", headers=owner, json={"channels": ["email"]}))
    stack.settle()
    mail = [n for n in stack.rows("notifications") if n.get("template") == "fund_statement"]
    assert mail and mail[0]["recipient"] == "asha@inv.sg" and base64.b64decode(mail[0]["attachments"][0]["data_b64"])[:4] == b"%PDF"
