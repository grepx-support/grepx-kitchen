# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""End to end: kitchen-bff over the kitchen services and the common services it reuses, on an in-memory Nexus.

The weekly and daily cycle of the BRD (section 9) for one business, with a second business that must never see it."""
from calendar import monthrange
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from grepx_config import load_config
from grepx_service.catalog import seed_catalog
from grepx_storage import LocalStorage
from grepx_testkit.stack import start_stack

from grepx_bff.gateway import Gateway
from main import create_app

ROOT = Path(__file__).resolve().parents[3]
COMMON = ["common-services/identity", "common-services/people-service", "common-services/notification-service",
          "common-services/template-service", "common-services/task-service", "common-services/audit-log-service",
          "common-services/settings-service", "common-services/scheduler-service", "common-services/lead-service"]
MONTH = date.today().isoformat()[:7]


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    stack = start_stack(ROOT, layers=(*COMMON, "product-services/kitchen"))
    assert all(seed_catalog(stack.requests, ROOT / "product-services/kitchen/catalog").values())
    gw = Gateway(stack.client, load_config(ROOT / "apps/kitchen-bff/config"), storage=LocalStorage(tmp_path_factory.mktemp("media")))
    api = TestClient(create_app(gw))
    op = stack.call("people_requests", "people-service", {"action": "CREATE", "name": "Gina Operator", "email": "ops@grepx.sg",
                                                           "phone": "+6591234567", "source": "staff"})
    assert op.ok, op.fields
    assert stack.call("auth_requests", "auth-service", {"action": "REGISTER", "user_id": op.fields["person_id"], "email": "ops@grepx.sg",
                                                        "password_enc": gw.box.seal("operator-pw")}).ok
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": op.fields["person_id"], "role": "admin"}).ok
    return stack, api


def login(api, email, password):
    r = api.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def ok(response):
    assert response.status_code == 200, response.text
    return response.json()


def test_the_weekly_and_daily_cycle(env):
    stack, api = env
    ops = login(api, "ops@grepx.sg", "operator-pw")
    hft = ok(api.post("/api/v1/platform/businesses", headers=ops, json={
        "name": "Halal Fusion Taco", "currency": "AUD", "timezone": "Australia/Sydney",
        "owner": {"name": "Omar Owner", "email": "owner@hft.au", "phone": "+61412345678", "password": "owner-pass"}}))
    ok(api.post("/api/v1/platform/businesses", headers=ops, json={
        "name": "Corner Cafe", "currency": "SGD", "timezone": "Asia/Singapore",
        "owner": {"name": "Cara Cafe", "email": "owner@cafe.sg", "phone": "+6598765432", "password": "cafe-pass"}}))
    assert len(ok(api.get("/api/v1/platform/businesses", headers=ops))) == 2
    owner = login(api, "owner@hft.au", "owner-pass")
    me = ok(api.get("/api/v1/me", headers=owner))
    assert me["tenant"] == hft["business_id"] and "manage_business" in me["perms"] and me["is_staff"] and me["role"] == "staff"
    assert api.get("/api/v1/platform/businesses", headers=owner).status_code == 403          # an owner is not the operator
    assert api.get("/api/v1/admin/access/system", headers=owner).status_code == 403

    # --- setup (BUS-02, KIT-01/02, ORD-01, ACC-01) ---
    loc = lambda **b: ok(api.post("/api/v1/setup/locations", headers=owner, json=b))["id"] if False else \
        ok(api.post("/api/v1/setup/locations", headers=owner, json=b))["location_id"]  # noqa: E731
    wh = loc(name="Central warehouse", kind="warehouse", days_of_cover=3)
    kit = loc(name="Kitchen", kind="kitchen")

    # --- platform support: the operator opens a business (read only by default, audited), never the other way round ---
    tok = lambda r: {"Authorization": f"Bearer {r['token']}"}  # noqa: E731
    look = ok(api.post(f"/api/v1/platform/businesses/{hft['business_id']}/support", headers=ops, json={}))
    assert look["read_only"] and look["business_name"] == "Halal Fusion Taco"
    seen = ok(api.get("/api/v1/me/business", headers=tok(look)))
    assert seen["support"] and seen["read_only"] and {l["id"] for l in seen["locations"]} == {wh, kit}
    assert len(ok(api.get("/api/v1/setup", headers=tok(look)))["locations"]) == 2                   # sees the owner's screens
    refused = api.post("/api/v1/setup/locations", headers=tok(look), json={"name": "Nope", "kind": "store"})
    assert refused.status_code == 403 and refused.json()["detail"]["reason"] == "READ_ONLY_SUPPORT"
    fix = ok(api.post(f"/api/v1/platform/businesses/{hft['business_id']}/support", headers=ops, json={"edit": True}))
    assert not fix["read_only"]
    assert api.post(f"/api/v1/platform/businesses/{hft['business_id']}/support", headers=tok(fix), json={}).status_code == 403   # no nesting
    assert api.post(f"/api/v1/platform/businesses/{hft['business_id']}/support", headers=owner, json={}).status_code == 403
    assert api.post("/api/v1/platform/businesses/nope/support", headers=ops, json={}).status_code == 404
    truck = loc(name="Events truck", kind="truck", days_of_cover=2)
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Fresh Meats", "phone": "+61400111222"}))["supplier_id"]
    item = lambda **b: ok(api.post("/api/v1/setup/items", headers=owner, json=b))["item_id"]  # noqa: E731
    beef = item(name="Beef chuck", kind="ingredient", unit="kg", cost=12, supplier_id=sup)
    lids = item(name="Lids", kind="supply", unit="pack", cost=4, supplier_id=sup)
    birria = item(name="Birria", kind="finished", unit="box", cost=6)
    ok(api.post("/api/v1/setup/recipes", headers=owner, json={"item_id": birria, "batch_output": 10, "ingredients": [{"item_id": beef, "qty": 4}]}))
    user = lambda email, role: ok(api.post("/api/v1/setup/users", headers=owner, json={  # noqa: E731
        "name": email.split("@")[0].title() + " Staff", "email": email, "phone": "+61412000111", "password": "staff-pass", "staff_role": role}))
    user("wes@hft.au", "warehouse"), user("kim@hft.au", "kitchen"), user("tia@hft.au", "closing"), user("dan@hft.au", "delivery")
    wes, kim, tia, dan = (login(api, f"{n}@hft.au", "staff-pass") for n in ("wes", "kim", "tia", "dan"))
    assert len(ok(api.get("/api/v1/setup", headers=owner))["users"]) == 5

    # --- weekly: order, receive (ORD-02..07) ---
    rec = ok(api.get(f"/api/v1/orders/recommendation?location_id={wh}", headers=wes))
    assert rec["has_history"] is False                                                     # ORD-10: type quantities by hand
    po = ok(api.post("/api/v1/orders", headers=wes, json={"supplier_id": sup, "location_id": wh, "lines": [{"item_id": beef, "qty": 40}]}))
    assert "Beef chuck: 40 kg" in po["text"] and "value" not in po                         # warehouse staff see no cost (COS-08)
    po = ok(api.post(f"/api/v1/orders/{po['po_id']}", headers=wes, json={"lines": [{"item_id": beef, "qty": 40}, {"item_id": lids, "qty": 5}]}))
    ok(api.post(f"/api/v1/orders/{po['po_id']}/receive", headers=wes, json={"lines": [{"item_id": beef, "qty": 38}, {"item_id": lids, "qty": 5}]}))
    stack.settle()
    levels = {(l["location_id"], l["item_id"]): l["qty"] for l in ok(api.get("/api/v1/stock", headers=wes))["levels"]}
    assert levels[(wh, beef)] == 38

    # --- daily: warehouse out, kitchen, transfer through the holding place, closing ---
    ok(api.post("/api/v1/stock/send", headers=wes, json={"from_location_id": wh, "to_location_id": kit, "lines": [{"item_id": beef, "qty": 16}]}))
    target = ok(api.get(f"/api/v1/kitchen/target?location_id={kit}", headers=kim))
    assert target["lines"][0]["source"] == "no_history"
    ok(api.post("/api/v1/kitchen/target", headers=owner, json={"item_id": birria, "qty": 40}))          # KIT-10
    target = ok(api.get(f"/api/v1/kitchen/target?location_id={kit}", headers=kim))
    assert (target["lines"][0]["target"], target["lines"][0]["batches"], target["ingredients"][0]["needed"]) == (40, 4, 16.0)
    ok(api.post("/api/v1/kitchen/use", headers=kim, json={"location_id": kit, "lines": [{"item_id": beef, "qty": 16}]}))
    ok(api.post("/api/v1/kitchen/production", headers=kim, json={"location_id": kit, "lines": [{"item_id": birria, "qty": 40}]}))
    assert len(ok(api.get(f"/api/v1/kitchen/today?location_id={kit}", headers=kim))["records"]) == 2
    ok(api.post("/api/v1/stock/transfer", headers=wes, json={"from_location_id": kit, "to_location_id": wh, "lines": [{"item_id": birria, "qty": 40}]}))
    ok(api.post("/api/v1/stock/send", headers=wes, json={"from_location_id": wh, "to_location_id": truck, "lines": [{"item_id": birria, "qty": 30}]}))
    trips = ok(api.get("/api/v1/stock/deliveries", headers=dan))["deliveries"]
    assert trips[0]["to"] == "Events truck" and trips[0]["lines"][0]["qty"] == 30
    assert trips[0]["state"] == "sent" and trips[0]["tracked"]                                         # delivery board
    assert ok(api.post(f"/api/v1/stock/deliveries/{trips[0]['id']}/delivered", headers=dan, json={}))["state"] == "delivered"
    assert ok(api.get("/api/v1/stock/deliveries", headers=dan))["deliveries"][0]["delivered_by"]
    places = [l["id"] for l in ok(api.get("/api/v1/setup", headers=owner))["locations"]]
    ok(api.post("/api/v1/setup/order", headers=owner, json={"list": "locations", "ids": places[::-1]}))  # dragged in setup
    assert [l["id"] for l in ok(api.get("/api/v1/setup", headers=owner))["locations"]] == places[::-1]
    assert api.post("/api/v1/setup/order", headers=wes, json={"list": "items", "ids": []}).status_code == 403
    assert api.get(f"/api/v1/kitchen/target?location_id={kit}", headers=dan).status_code == 403            # not the production plan

    form = ok(api.get(f"/api/v1/closing/form?location_id={truck}", headers=tia))
    assert {l["item_id"]: l["expected"] for l in form["lines"]}[birria] == 30 and form["sales_types"] == ["Sales", "Other sales"]
    closing = ok(api.post("/api/v1/closing", headers=tia, json={"location_id": truck, "issues": "Generator noisy",
                                                                "counts": [{"item_id": birria, "qty": 6}], "sales": {"Sales": 600, "Other sales": 120}}))
    assert closing["total_sales"] == 720 and closing["staff_name"] == "Tia Staff"
    stack.settle()
    assert api.post("/api/v1/closing", headers=tia, json={"location_id": truck, "counts": []}).json()["detail"]["reason"] == "ALREADY_SUBMITTED"

    # --- costs (COS-03..09) ---
    assert api.get(f"/api/v1/costs/days?month={MONTH}", headers=tia).status_code == 403
    day = ok(api.get(f"/api/v1/costs/days?month={MONTH}", headers=owner))["days"][0]
    assert (day["ingredient_cost"], day["cogs_pct"], day["out_of_range"]) == (144, 20.0, True)          # 24 boxes x 6 / 720; range 25-35
    month = ok(api.get(f"/api/v1/costs/month?month={MONTH}", headers=owner))
    assert month["net_profit"] is None and "labour" in month["missing"]                                 # never a profit with a gap
    ok(api.post("/api/v1/setup/overheads", headers=owner, json={"location_id": truck, "month": MONTH, "labour": 3000, "rent": 0, "other": 300}))
    month = ok(api.get(f"/api/v1/costs/month?month={MONTH}&location_id={truck}", headers=owner))
    assert month["complete"] and month["overheads_days"] >= 1                                        # running month: to date
    assert month["labour"] == round(3000 * month["overheads_days"] / monthrange(int(MONTH[:4]), int(MONTH[5:]))[1], 2)
    assert month["net_profit"] == round(720 - 144 - month["labour"] - month["rent"] - month["other"], 2)
    diffs = ok(api.get("/api/v1/closing/history", headers=owner))["closings"][0]["counts"]
    assert diffs[0]["difference"] == -24                                                                 # Q6: the owner reviews it

    # --- roles: who may adjust stock (ACC-03), modules on/off (BUS-03) ---
    adjust = {"location_id": truck, "lines": [{"item_id": birria, "qty": 5}], "note": "Recount after spill"}
    assert api.post("/api/v1/stock/adjust", headers=tia, json=adjust).status_code == 403
    ok(api.post("/api/v1/setup/roles/closing", headers=owner, json={"perms": ["closing", "adjust_stock"]}))
    assert ok(api.post("/api/v1/stock/adjust", headers=tia, json=adjust))["changes"][0]["qty"] == -1
    moves = ok(api.get(f"/api/v1/stock/movements?location_id={truck}", headers=owner))["movements"]
    assert moves[0]["kind"] == "adjust" and moves[0]["user_name"] == "Tia Staff" and moves[0]["note"] == "Recount after spill"   # ACC-05
    ok(api.patch("/api/v1/setup/business", headers=owner, json={"modules": {"kitchen": False}}))
    assert api.get(f"/api/v1/kitchen/target?location_id={kit}", headers=kim).json()["detail"]["reason"] == "MODULE_OFF"

    # --- another business sees none of it (BUS-05) ---
    cafe = login(api, "owner@cafe.sg", "cafe-pass")
    assert ok(api.get("/api/v1/stock", headers=cafe))["levels"] == []
    assert ok(api.get("/api/v1/setup", headers=cafe))["locations"] == []
    assert api.get(f"/api/v1/orders/{po['po_id']}", headers=cafe).status_code == 404
    bad = api.post("/api/v1/stock/receive", headers=cafe, json={"location_id": wh, "lines": [{"item_id": beef, "qty": 1}]})
    assert bad.json()["detail"]["reason"] == "UNKNOWN_LOCATION"
    assert api.post("/api/v1/setup/roles/closing", headers=cafe, json={"perms": ["adjust_stock"]}).status_code == 200   # its own copy
    assert ok(api.get("/api/v1/me/business", headers=cafe))["business"]["currency"] == "SGD"


def test_web_shell_and_product_screens(env):
    _, api = env
    assert api.get("/").status_code == 200 and "app.js" in api.get("/").text
    assert api.get("/product.json").json()["name"]
    assert api.get("/assets/modules/kitchen/today.js").status_code == 200
    assert api.get("/assets/modules/core/auth.js").status_code == 200


def test_warehouse_floor_runs_inventory_and_messages(env, monkeypatch):
    """Lots with expiry -> FEFO pick list -> delivery run with proof of delivery -> stock take, alerts, valuation,
    waste in cost, purchase order sent (test mode: logged in the outbox), and the public demo form."""
    stack, api = env
    ops = login(api, "ops@grepx.sg", "operator-pw")
    ok(api.post("/api/v1/platform/businesses", headers=ops, json={
        "name": "Green Bowl", "currency": "SGD", "timezone": "Asia/Singapore",
        "owner": {"name": "Gail Bowl", "email": "owner@bowl.sg", "phone": "+6591110000", "password": "bowl-pass"}}))
    owner = login(api, "owner@bowl.sg", "bowl-pass")
    loc = lambda **b: ok(api.post("/api/v1/setup/locations", headers=owner, json=b))["location_id"]  # noqa: E731
    wh, shop = loc(name="Store", kind="warehouse"), loc(name="Shop", kind="store")
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Dairy Co", "phone": "+6590001111", "email": "orders@dairy.example"}))["supplier_id"]
    milk = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Milk", "kind": "ingredient", "unit": "l", "cost": 2,
                                                                    "supplier_id": sup, "shelf_life_days": 5, "barcode": "9555 0001"}))["item_id"]
    found = {i["id"]: i for i in ok(api.get("/api/v1/stock/items", headers=owner))["items"]}[milk]
    assert (found["barcode"], found["shelf_life_days"]) == ("95550001", 5)

    # --- warehouse floor: bins, lots with expiry (FEFO) ---
    bin_a = ok(api.post("/api/v1/warehouse/bins", headers=owner, json={"location_id": wh, "code": "A-01", "zone": "chilled"}))["bin_id"]
    soon, later = date.fromordinal(date.today().toordinal() + 1).isoformat(), date.fromordinal(date.today().toordinal() + 9).isoformat()
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": milk, "qty": 10, "expiry": later, "bin_id": bin_a}]}))
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": milk, "qty": 6, "expiry": soon, "lot_code": "B7"}]}))
    stack.settle()
    floor = ok(api.get(f"/api/v1/warehouse?location_id={wh}", headers=owner))
    assert [(l["qty"], l["expiry"]) for l in floor["lots"]] == [(6, soon), (10, later)]                 # soonest first
    assert floor["lots"][1]["bin_code"] == "A-01"

    pick = ok(api.post("/api/v1/warehouse/picks", headers=owner, json={"from_location_id": wh, "to_location_id": shop, "lines": [{"item_id": milk, "qty": 8}]}))
    sheet = ok(api.get(f"/api/v1/warehouse/picks/{pick['pick_id']}", headers=owner))
    assert [x["qty"] for x in sheet["lines"][0]["lots"]] == [6, 2]                                      # first expiry, first out
    ok(api.post(f"/api/v1/warehouse/picks/{pick['pick_id']}/pick", headers=owner, json={"item_id": milk, "qty": 8}))
    ok(api.post(f"/api/v1/warehouse/picks/{pick['pick_id']}/complete", headers=owner))
    stack.settle()
    lots = ok(api.get(f"/api/v1/warehouse?location_id={wh}", headers=owner))["lots"]
    assert [(l["qty"], l["expiry"]) for l in lots] == [(8, later)]

    # --- delivery run with proof of delivery ---
    board = ok(api.get("/api/v1/runs", headers=owner))
    assert board["waiting"][0]["to"] == "Shop"
    run = ok(api.post("/api/v1/runs", headers=owner, json={"date": date.today().isoformat(), "start_time": "09:00", "name": "Morning",
                                                           "delivery_ids": [board["waiting"][0]["id"]], "drive_minutes": 20}))
    assert run["stops"][0]["eta"] and not ok(api.get("/api/v1/runs", headers=owner))["waiting"]
    ok(api.post(f"/api/v1/runs/{run['run_id']}/start", headers=owner))
    stop = run["stops"][0]["stop_id"]
    done = ok(api.post(f"/api/v1/runs/{run['run_id']}/stops/{stop}/deliver", headers=owner,
                       json={"receiver": "Sam at the shop", "signature": "data:image/png;base64,AAAA"}))
    assert done["state"] == "done" and done["stops"][0]["receiver"] == "Sam at the shop"
    stack.settle()
    assert ok(api.get("/api/v1/stock/deliveries", headers=owner))["deliveries"][0]["state"] == "delivered"

    # --- inventory control: par -> alert, stock take, valuation, analysis with waste ---
    ok(api.post("/api/v1/inventory/par", headers=owner, json={"location_id": wh, "item_id": milk, "min": 20, "max": 40}))
    ok(api.post("/api/v1/inventory/alerts/check", headers=owner))
    stack.settle()
    alerts = ok(api.get("/api/v1/inventory/alerts", headers=owner))["alerts"]
    assert [(a["kind"], a["fill_to"]) for a in alerts if a["location_id"] == wh] == [("low", 40)]
    assert {(a["kind"], a["location_id"]) for a in alerts} == {("low", wh), ("expiring", shop)}       # the 6 l moved there expire tomorrow
    low = next(a for a in alerts if a["kind"] == "low")
    ok(api.post(f"/api/v1/inventory/alerts/{low['id']}/done", headers=owner))
    stack.settle()
    assert [a["kind"] for a in ok(api.get("/api/v1/inventory/alerts", headers=owner))["alerts"]] == ["expiring"]

    take = ok(api.post("/api/v1/inventory/takes", headers=owner, json={"location_id": wh, "blind": True}))
    ok(api.post(f"/api/v1/inventory/takes/{take['take_id']}/count", headers=owner, json={"lines": [{"item_id": milk, "qty": 7}]}))
    take = ok(api.post(f"/api/v1/inventory/takes/{take['take_id']}/finish", headers=owner))
    assert (take["state"], take["lines_changed"], take["variance_value"]) == ("done", 1, -2)            # 1 l short at 2
    stack.settle()
    ok(api.post("/api/v1/stock/waste", headers=owner, json={"location_id": wh, "reason": "spoiled", "lines": [{"item_id": milk, "qty": 2}]}))
    stack.settle()
    assert ok(api.get(f"/api/v1/inventory/valuation?location_id={wh}", headers=owner))["total"] == 10   # 5 l at 2 (the shop has 8 more)
    analysis = ok(api.get("/api/v1/inventory/analysis?days=30", headers=owner))
    assert analysis["waste"]["spoiled"] == 4

    # --- messages: purchase order to the supplier, logged in the outbox (test mode) ---
    po = ok(api.post("/api/v1/orders", headers=owner, json={"supplier_id": sup, "location_id": wh, "lines": [{"item_id": milk, "qty": 30}]}))
    sent = ok(api.post(f"/api/v1/orders/{po['po_id']}/send", headers=owner, json={"channels": ["email", "whatsapp"]}))
    assert sent["sent"][0]["channels"] == ["email", "whatsapp"]
    stack.settle()
    box = ok(api.get("/api/v1/outbox", headers=owner))["messages"]
    assert {m["channel"] for m in box if m["template"] == "purchase_order"} == {"email", "whatsapp"}
    ok(api.post("/api/v1/platform/businesses", headers=ops, json={"name": "Other Bowl", "currency": "SGD", "timezone": "Asia/Singapore",
        "owner": {"name": "Otto Other", "email": "owner@other.sg", "phone": "+6591110001", "password": "other-pass"}}))
    other = login(api, "owner@other.sg", "other-pass")
    assert not [m for m in ok(api.get("/api/v1/outbox", headers=other))["messages"] if m["template"] == "purchase_order"]

    # --- public demo form (no login) -> the operator's list ---
    monkeypatch.setenv("LEADS_NOTIFY_EMAIL", "sales@grepx.sg")
    ok(api.post("/api/v1/public/demo", json={"name": "Lee Chef", "email": "lee@example.com", "company": "Noodle Bar", "size": "2-5"}))
    stack.settle()
    lead = ok(api.get("/api/v1/platform/leads", headers=ops))["leads"][0]
    assert (lead["name"], lead["stage"]) == ("Lee Chef", "new")
    assert ok(api.post(f"/api/v1/platform/leads/{lead['id']}", headers=ops, json={"stage": "contacted"}))["stage"] == "contacted"
    assert api.get("/api/v1/platform/leads", headers=owner).status_code == 403
    assert api.post("/api/v1/public/demo", json={"name": "Bot", "email": "bot@example.com", "website": "http://spam"}).status_code != 500
