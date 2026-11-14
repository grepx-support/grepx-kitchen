# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""API keys through the kitchen API: made once, a read key reads only, a write key writes as the business, revoked
keys stop working, another business's data is never reachable."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_api_keys(env):
    stack, api = env
    owner = open_business(api, "Key Kitchen", "owner@keys.sg")["owner"]
    open_business(api, "Other Keys", "owner@otherkeys.sg")
    read = ok(api.post("/api/v1/setup/api-keys", headers=owner, json={"name": "Website", "scope": "read"}))
    write = ok(api.post("/api/v1/setup/api-keys", headers=owner, json={"name": "POS", "scope": "write"}))
    assert read["key"].startswith("gx_") and read["scope"] == "read"
    stack.settle()
    listed = ok(api.get("/api/v1/setup/api-keys", headers=owner))["keys"]
    assert {k["name"] for k in listed} == {"Website", "POS"} and all("secret_hash" not in k for k in listed)
    as_read, as_write = {"X-Api-Key": read["key"]}, {"Authorization": f"Bearer {write['key']}"}
    assert ok(api.get("/api/v1/stock/items", headers=as_read))["items"] == []
    assert api.post("/api/v1/setup/items", headers=as_read, json={"name": "Salt", "kind": "ingredient", "unit": "kg"}).status_code == 403
    ok(api.post("/api/v1/setup/items", headers=as_write, json={"name": "Salt", "kind": "ingredient", "unit": "kg"}))
    assert [i["name"] for i in ok(api.get("/api/v1/stock/items", headers=owner))["items"]] == ["Salt"]
    assert api.get("/api/v1/stock/items", headers={"X-Api-Key": read["key"][:-2] + "zz"}).status_code == 401
    ok(api.delete(f"/api/v1/setup/api-keys/{read['key_id']}", headers=owner))
    stack.settle()
    assert api.get("/api/v1/stock/items", headers=as_read).status_code == 401
