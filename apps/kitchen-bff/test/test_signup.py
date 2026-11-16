# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Self-service sign-up of a kitchen business: details -> email link + phone code -> the business is set up with its owner signed in, its
short name is its address (/b/<name>); the operator sees the sign-up and the messages that only went to the log."""
from kitchen_stack import env, login, ok  # noqa: F401

ME = {"business_name": "Spice Hub Kitchens", "slug": "spicehub", "owner_name": "Ravi Kumar", "email": "ravi@spicehub.au",
      "phone": "+91 98450 12345", "password": "spicehub-pass", "currency": "AUD", "timezone": "Australia/Sydney", "accept_terms": True}


def sent(stack, template):
    rows = [r for r in stack.rows("notifications") if r.get("template") == template]
    return rows[-1]["values"]


def test_a_kitchen_signs_up_itself(env):
    stack, api = env
    assert ok(api.get("/api/v1/public/signup/check?slug=spicehub")) == {"slug": "spicehub", "available": True, "problem": ""}
    assert api.post("/api/v1/public/signup", json={**ME, "password": "short"}).json()["detail"]["reason"] == "WEAK_PASSWORD"
    assert api.post("/api/v1/public/signup", json={**ME, "accept_terms": False}).json()["detail"]["reason"] == "ACCEPT_TERMS"
    assert api.post("/api/v1/public/signup", json={**ME, "slug": "admin"}).json()["detail"]["reason"] == "RESERVED_SLUG"
    signup = ok(api.post("/api/v1/public/signup", json=ME))["signup"]
    sid = signup["signup_id"]
    assert (signup["stage"], signup["email"], signup["phone"]) == ("pending", "ra**@spicehub.au", "+91*******345")
    stack.settle()
    link, code = sent(stack, "signup_email")["link"], sent(stack, "signup_code")["code"]
    assert "/#/signup/email?signup=" in link
    assert ok(api.get("/api/v1/public/signup/check?slug=spicehub"))["problem"] == "SLUG_TAKEN"

    # the operator sees it, with the link and the code that went to the log (no email / SMS provider in tests)
    ops = login(api, "ops@grepx.sg", "operator-pw")
    listed = ok(api.get("/api/v1/platform/signups", headers=ops))["signups"][0]
    assert listed["email"] == "ravi@spicehub.au" and any(code in m["text"] for m in listed["logged"])
    assert api.get("/api/v1/platform/signups", headers=None).status_code == 401

    wrong = api.post(f"/api/v1/public/signup/{sid}/phone", json={"code": "000000" if code != "000000" else "111111"})
    assert wrong.json()["detail"]["reason"] == "WRONG_CODE"
    half = ok(api.post(f"/api/v1/public/signup/{sid}/phone", json={"code": code}))
    assert half["signup"]["phone_ok"] and not half.get("done")
    assert api.post(f"/api/v1/public/signup/{sid}/email", json={"token": "nope"}).json()["detail"]["reason"] == "WRONG_LINK"
    done = ok(api.post(f"/api/v1/public/signup/{sid}/email", json={"token": link.split("token=")[1]}))
    assert done["done"] and done["slug"] == "spicehub" and done["session"]["token"]

    # the owner is signed in to their own business, as its owner
    owner = {"Authorization": f"Bearer {done['session']['token']}"}
    me = ok(api.get("/api/v1/me", headers=owner))
    assert me["tenant"] == done["business_id"]
    assert ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": "Central warehouse", "kind": "warehouse"}))["location_id"]
    login(api, "ravi@spicehub.au", "spicehub-pass")

    # its address; the operator renames it and the old one leads to the new
    assert ok(api.get("/api/v1/public/address/spicehub")) == {"slug": "spicehub", "name": "Spice Hub Kitchens", "product": "kitchen", "moved": False}
    ok(api.post("/api/v1/platform/addresses", headers=ops, json={"business_id": done["business_id"], "slug": "spicehub-kitchens"}))
    assert ok(api.get("/api/v1/public/address/spicehub"))["slug"] == "spicehub-kitchens"
    assert api.get("/api/v1/public/address/nobody-here").status_code == 404

    # the same email cannot open a second business; finishing twice does nothing
    assert api.post("/api/v1/public/signup", json={**ME, "slug": "spicehub-two"}).json()["detail"]["reason"] == "EMAIL_IN_USE"
    assert api.post(f"/api/v1/public/signup/{sid}/finish").status_code == 409
    assert api.get("/b/spicehub").status_code == 200                 # the web app answers the business's address
