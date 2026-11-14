# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Round 4: big orders wait for the owner, supplier price jumps are flagged and told, one approvals inbox."""
from kitchen_stack import env, login, ok, open_business  # noqa: F401


def test_approvals_inbox_and_price_jumps(env):
    stack, api = env
    owner = open_business(api, "Approve Kitchen", "owner@approve.sg")["owner"]
    ok(api.patch("/api/v1/setup/business", headers=owner, json={"settings": {"po_approval_over": 100, "price_jump_pct": 10}}))
    wh = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Store", "kind": "warehouse"}))["location_id"]
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Fish Co", "email": "fish@co.sg"}))["supplier_id"]
    fish = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Salmon", "kind": "ingredient", "unit": "kg", "cost": 20, "supplier_id": sup}))["item_id"]
    ok(api.post("/api/v1/setup/users", headers=owner, json={"name": "Wes Staff", "email": "wes@approve.sg", "phone": "+6590000002",
                                                            "password": "staff-pass", "staff_role": "warehouse"}))
    wes = login(api, "wes@approve.sg", "staff-pass")
    # --- an order above the owner's amount: staff cannot send it, see no money, owner approves from the inbox ---
    po = ok(api.post("/api/v1/orders", headers=wes, json={"supplier_id": sup, "location_id": wh, "lines": [{"item_id": fish, "qty": 10}]}))
    assert po["approval"] == {"state": "pending"} and "value" not in po
    refused = api.post(f"/api/v1/orders/{po['po_id']}/send", headers=wes, json={"channels": ["email"]})
    assert refused.status_code == 409 and refused.json()["detail"]["reason"] == "NEEDS_APPROVAL"
    assert api.post(f"/api/v1/orders/{po['po_id']}/approve", headers=wes, json={"approve": True}).status_code == 403
    box = ok(api.get("/api/v1/approvals", headers=owner))
    assert box["orders"][0]["value"] == 200 and box["waiting"] == 1
    assert ok(api.get("/api/v1/approvals", headers=wes)) == {"orders": [], "bills": [], "leave": [], "rises": [], "waiting": 0}
    ok(api.post(f"/api/v1/orders/{po['po_id']}/approve", headers=owner, json={"approve": True}))
    ok(api.post(f"/api/v1/orders/{po['po_id']}/send", headers=wes, json={"channels": ["email"]}))
    # --- bills: the second one is 15 % dearer - flagged on the bill, in the inbox, and the owner is told ---
    ok(api.post("/api/v1/bills", headers=owner, json={"supplier_id": sup, "supplier_ref": "F-1", "bill_date": "2026-11-01",
                                                      "lines": [{"item_id": fish, "qty": 10, "unit_price": "20"}]}))
    ok(api.post("/api/v1/bills", headers=owner, json={"supplier_id": sup, "supplier_ref": "F-2", "bill_date": "2026-11-10",
                                                      "lines": [{"item_id": fish, "qty": 10, "unit_price": "23"}]}))
    stack.settle()
    box = ok(api.get("/api/v1/approvals", headers=owner))
    assert [b["supplier_ref"] for b in box["bills"]] == ["F-2", "F-1"] and box["bills"][0]["jumps"] == 1     # the jump first
    rise = ok(api.get(f"/api/v1/approvals/prices?item_id={fish}&days=3650", headers=owner))
    assert [p["price"] for p in rise["points"]] == [2000, 2300] and rise["rises"][0]["pct"] == 15.0
    told = [n for n in stack.rows("notifications") if n.get("template") == "price_jump"]
    assert told and told[0]["recipient"] == "owner@approve.sg"
