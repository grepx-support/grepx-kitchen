# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Round 1: the business logo on its documents, purchase orders and payslips sent with the PDF attached."""
import base64
import io

from PIL import Image

from kitchen_stack import env, ok, open_business  # noqa: F401


def logo_url() -> str:
    out = io.BytesIO()
    Image.new("RGBA", (400, 120), (13, 148, 136, 255)).save(out, "PNG")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()


def sent(stack, template: str) -> list[dict]:
    stack.settle()
    return [n for n in stack.rows("notifications") if n.get("template") == template]


def test_logo_orders_and_payslips_leave_with_their_pdf(env, monkeypatch):
    monkeypatch.setenv("SITE_URL", "https://kitchen.example")
    stack, api = env
    biz = open_business(api, "Logo Bistro", "owner@logo.sg")
    owner = biz["owner"]
    plain = api.get("/api/v1/pdf/count-sheet?location_id=x", headers=owner).content
    assert b"/Subtype /Image" not in plain
    # --- logo: uploaded once, printed on every document; refused when it is not a picture ---
    assert api.post("/api/v1/setup/logo", headers=owner, json={"image": "data:text/plain;base64,aGk="}).status_code == 400
    made = ok(api.post("/api/v1/setup/logo", headers=owner, json={"image": logo_url()}))
    assert made["business"]["billing"]["logo_id"] == made["logo_id"]
    assert api.get(f"/api/v1/media/{made['logo_id']}").headers["content-type"] == "image/png"
    wh = ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Store", "kind": "warehouse"}))["location_id"]
    sup = ok(api.post("/api/v1/setup/suppliers", headers=owner, json={"name": "Veg Co", "email": "orders@veg.sg", "phone": "+6561230000"}))["supplier_id"]
    leek = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Leek", "kind": "ingredient", "unit": "kg", "cost": 3, "supplier_id": sup}))["item_id"]
    po = ok(api.post("/api/v1/orders", headers=owner, json={"supplier_id": sup, "location_id": wh, "lines": [{"item_id": leek, "qty": 9}]}))
    assert b"/Subtype /Image" in api.get(f"/api/v1/pdf/order/{po['po_id']}", headers=owner).content
    # --- the order goes out with its PDF: bytes for email, a working link for WhatsApp ---
    ok(api.post(f"/api/v1/orders/{po['po_id']}/send", headers=owner, json={"channels": ["email", "whatsapp"]}))
    msgs = sent(stack, "purchase_order")
    assert {m["channel"] for m in msgs} == {"email", "whatsapp"} and all(m["delivery"] == "LOGGED" for m in msgs)
    file = msgs[0]["attachments"][0]
    assert file["mime"] == "application/pdf" and base64.b64decode(file["data_b64"])[:4] == b"%PDF"
    link = file["url"].removeprefix("https://kitchen.example")
    got = api.get(link)
    assert got.status_code == 200 and got.content[:4] == b"%PDF" and api.get(link[:-5] + "x.pdf").status_code == 404
    # --- payslips: only once the month is locked, to whoever can be reached, each send kept ---
    emp = lambda **b: ok(api.post("/api/v1/team", headers=owner, json={"home_site": wh, "position": "Cook", **b}))["employee_id"]  # noqa: E731
    lim = emp(name="Lim Wei", email="lim@logo.sg", pay={"basis": "monthly", "rate": 3000})
    tan = emp(name="Tan Ah Kow", pay={"basis": "monthly", "rate": 2800})
    ok(api.post("/api/v1/payroll/run", headers=owner, json={"month": "2026-11"}))
    early = ok(api.post("/api/v1/payroll/payslips/send", headers=owner, json={"month": "2026-11", "channels": ["email"]}))
    assert early["sent"] == 0 and {r["reason"] for r in early["results"]} == {"MONTH_NOT_FINAL"}
    ok(api.post("/api/v1/payroll/finalise", headers=owner, json={"month": "2026-11"}))
    out = ok(api.post("/api/v1/payroll/payslips/send", headers=owner, json={"month": "2026-11", "channels": ["email", "whatsapp"]}))
    by = {r["employee_id"]: r for r in out["results"]}
    assert out["sent"] == 1 and by[lim]["channels"] == ["email"] and by[tan]["reason"] == "NO_CONTACT"
    slip = sent(stack, "payslip")
    assert len(slip) == 1 and slip[0]["recipient"] == "lim@logo.sg" and "Net pay" in slip[0]["body"]
    assert base64.b64decode(slip[0]["attachments"][0]["data_b64"])[:4] == b"%PDF"
    assert ok(api.get("/api/v1/payroll?month=2026-11", headers=owner))["payslips"][0]["sent"][0]["channels"] == ["email"]
    ok(api.delete("/api/v1/setup/logo", headers=owner))
    assert b"/Subtype /Image" not in api.get(f"/api/v1/pdf/order/{po['po_id']}", headers=owner).content
