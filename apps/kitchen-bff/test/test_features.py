# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Setup -> Features: a feature switched off refuses its API and is off in /me (the web hides its pages)."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_switching_features_off_and_on(env):
    stack, api = env
    owner = open_business(api, "Feature Kitchen", "owner@features.sg")["owner"]
    assert ok(api.get("/api/v1/me", headers=owner))["features"].get("funds") is True
    ok(api.patch("/api/v1/setup/business", headers=owner, json={"modules": {"funds": False, "payroll": False}}))
    me = ok(api.get("/api/v1/me", headers=owner))
    assert me["features"]["funds"] is False and me["features"]["payroll"] is False and me["features"]["quotes"] is True
    for path in ("/api/v1/funds", "/api/v1/payroll?month=2026-11"):
        r = api.get(path, headers=owner)
        assert r.status_code == 403 and r.json()["detail"]["reason"] == "MODULE_OFF"
    assert api.get("/api/v1/sales/quotes", headers=owner).status_code == 200
    ok(api.patch("/api/v1/setup/business", headers=owner, json={"modules": {"funds": True}}))
    assert api.get("/api/v1/funds", headers=owner).status_code == 200



def test_item_picture_on_the_recipe_card(env):
    import base64
    import io

    from PIL import Image
    stack, api = env
    owner = open_business(api, "Picture Kitchen", "owner@pictures.sg")["owner"]
    dish = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Masala dosa", "kind": "finished", "unit": "each", "cost": 1}))["item_id"]
    out = io.BytesIO()
    Image.new("RGB", (800, 600), (200, 120, 40)).save(out, "JPEG")
    saved = ok(api.post(f"/api/v1/setup/items/{dish}/picture", headers=owner, json={"image": "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode()}))
    assert saved["image_id"] and api.get(f"/api/v1/media/{saved['image_id']}").status_code == 200
    assert ok(api.get(f"/api/v1/chef/recipes/{dish}", headers=owner))["recipe"]["image_id"] == saved["image_id"]
    assert ok(api.post(f"/api/v1/setup/items/{dish}/picture", headers=owner, json={"remove": True}))["image_id"] == ""
