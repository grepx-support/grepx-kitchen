# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 1 - what an owner sets up once: the business (by the platform operator), places, suppliers, items, recipes,
staff with their roles, monthly costs. All through the site's API."""
from __future__ import annotations

from datetime import date, timedelta

import data


def month_before(d: date) -> str:
    return (d.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")


def create(site, ops_email: str, ops_password: str, say) -> dict:
    """Returns ids: {"tenant", "place": {key: id}, "item": {key: id}, "supplier": {key: id}, "user": {email: id}}."""
    site.login("ops", ops_email, ops_password)
    biz = site.post("/platform/businesses", {**data.BUSINESS, "owner": {**data.OWNER, "password": data.PASSWORD}}, "ops")
    say(f"business {data.BUSINESS['name']} created with its owner and roles")
    site.login("owner", data.OWNER["email"], data.PASSWORD)
    ids = {"tenant": biz["business_id"], "place": {}, "item": {}, "supplier": {}, "user": {}}
    for key, name, kind, holding, address in data.PLACES:
        ids["place"][key] = site.post("/setup/locations", {"name": name, "kind": kind, "holding": holding, "address": address,
                                                            "days_of_cover": 3, "count_every_days": 1}, "owner")["location_id"]
    for key, name, phone, contact in data.SUPPLIERS:
        ids["supplier"][key] = site.post("/setup/suppliers", {"name": name, "phone": phone, "contact": contact,
                                                                  "email": data.SUPPLIER_EMAIL.format(key=key)}, "owner")["supplier_id"]
    for key, name, kind, unit, cost, sup, category in data.ITEMS:
        ids["item"][key] = site.post("/setup/items", {"name": name, "kind": kind, "unit": unit, "cost": cost, "category": category,
                                                      "supplier_id": ids["supplier"].get(sup, ""),
                                                      "shelf_life_days": data.SHELF_LIFE.get(key), "barcode": data.BARCODE.get(key, "")}, "owner")["item_id"]
    for product, (output, parts) in data.RECIPES.items():
        site.post("/setup/recipes", {"item_id": ids["item"][product], "batch_output": output,
                                     "ingredients": [{"item_id": ids["item"][k], "qty": q} for k, q in parts.items()]}, "owner")
    say(f"{len(data.PLACES)} places, {len(data.SUPPLIERS)} suppliers, {len(data.ITEMS)} items, {len(data.RECIPES)} recipes")
    for role, name, email in data.STAFF:
        phone = f"+614000000{10 + len(ids['user'])}"
        ids["user"][email] = site.post("/setup/users", {"name": name, "email": email, "phone": phone, "password": data.PASSWORD,
                                                        "staff_role": role}, "owner")["user_id"]
        site.login(email, email, data.PASSWORD)
    today = date.today()
    for month in (month_before(today), today.strftime("%Y-%m")):
        for key, (labour, rent, other) in data.OVERHEADS.items():
            site.post("/setup/overheads", {"location_id": ids["place"][key], "month": month, "labour": labour, "rent": rent, "other": other}, "owner")
    say(f"{len(data.STAFF)} staff logins and monthly costs for two months")
    return ids
