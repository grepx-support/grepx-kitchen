# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 1 - what an owner sets up once: the business (by the platform operator), places, suppliers, items, recipes,
staff with their roles, monthly costs. All through the site's API."""
from __future__ import annotations

from datetime import date, timedelta


def months_back(today: date, n: int) -> list[str]:
    """The last n months, oldest first, this month last."""
    y, m, out = today.year, today.month, []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return list(reversed(out))


SPLIT = {"labour": [("Salaries and wages", .82), ("Overtime and casual staff", .06), ("Staff meals", .04), ("Staff benefits (PF / CPF / super)", .08)],
         "rent": [("Rent", .9), ("Service charge / maintenance", .1)],
         "other": [("Electricity", .3), ("Gas", .12), ("Water", .04), ("Delivery-app commission", .28), ("Internet and phone", .05),
                   ("Repairs and maintenance", .11), ("Cleaning and pest control", .1)]}


def cost_lines(labour: float, rent: float, other: float) -> list[dict]:
    """A place's three monthly amounts as the cost lines an owner would enter."""
    amounts = {"labour": labour, "rent": rent, "other": other}
    return [{"category": c, "group": g, "amount": round(amounts[g] * share, 2)} for g, parts in SPLIT.items() for c, share in parts]


def monthly_costs(site, d, ids: dict) -> None:
    """Six months of each place's costs as lines (creeping up a little each month), and the accountant's fee shared
    over the places by sales: Funds links them to the money each place was given."""
    for n, month in enumerate(months_back(date.today(), 6)):
        lift = 1 + 0.03 * n
        for key, (labour, rent, other) in d.OVERHEADS.items():
            site.post("/setup/overheads", {"location_id": ids["place"][key], "month": month, "lines": cost_lines(labour * lift, rent, other * lift)}, "owner")
        fee = round(sum(sum(v) for v in d.OVERHEADS.values()) * 0.02, -2)
        site.post("/setup/overheads/share", {"month": month, "category": "Accountant", "group": "other", "amount": fee, "rule": "equal",
                                             "location_ids": [ids["place"][k] for k in d.OVERHEADS], "note": "monthly bookkeeping"}, "owner")


def month_before(d: date) -> str:
    return (d.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")


def staff(d, role: str) -> tuple[str, str]:
    """(name, email) of the demo person with this staff role."""
    return next((name, email) for r, name, email in d.STAFF if r == role)


def create(site, d, ops_email: str, ops_password: str, say) -> dict:
    """Returns ids: {"tenant", "place": {key: id}, "item": {key: id}, "supplier": {key: id}, "user": {email: id}}."""
    site.login("ops", ops_email, ops_password)
    biz = site.post("/platform/businesses", {**d.BUSINESS, "owner": {**d.OWNER, "password": d.PASSWORD}}, "ops")
    say(f"business {d.BUSINESS['name']} created with its owner and roles")
    site.login("owner", d.OWNER["email"], d.PASSWORD)
    ids = {"tenant": biz["business_id"], "place": {}, "item": {}, "supplier": {}, "user": {}}
    for key, name, kind, holding, address in d.PLACES:
        ids["place"][key] = site.post("/setup/locations", {"name": name, "kind": kind, "holding": holding, "address": address,
                                                            "days_of_cover": 3, "count_every_days": 1}, "owner")["location_id"]
    for key, name, phone, contact in d.SUPPLIERS:
        ids["supplier"][key] = site.post("/setup/suppliers", {"name": name, "phone": phone, "contact": contact,
                                                                  "email": d.SUPPLIER_EMAIL.format(key=key)}, "owner")["supplier_id"]
    for key, name, kind, unit, cost, sup, category in d.ITEMS:
        ids["item"][key] = site.post("/setup/items", {"name": name, "kind": kind, "unit": unit, "cost": cost, "category": category,
                                                      "supplier_id": ids["supplier"].get(sup, ""),
                                                      "shelf_life_days": d.SHELF_LIFE.get(key), "barcode": d.BARCODE.get(key, ""),
                                                      "price": d.WHOLESALE.get(key, 0), "diet": getattr(d, "MARKS", {}).get(key, ("", []))[0],
                                                      "allergens": getattr(d, "MARKS", {}).get(key, ("", []))[1]}, "owner")["item_id"]
    for product, (output, parts) in d.RECIPES.items():
        site.post("/setup/recipes", {"item_id": ids["item"][product], "batch_output": output,
                                     "ingredients": [{"item_id": ids["item"][k], "qty": q} for k, q in parts.items()]}, "owner")
        if product in getattr(d, "CARDS", {}):
            site.put(f"/chef/recipes/{ids['item'][product]}/card", d.CARDS[product], "owner")
    say(f"{len(d.PLACES)} places, {len(d.SUPPLIERS)} suppliers, {len(d.ITEMS)} items, {len(d.RECIPES)} recipes")
    for role, name, email in d.STAFF:
        phone = d.PHONE.format(n=10 + len(ids["user"]))
        ids["user"][email] = site.post("/setup/users", {"name": name, "email": email, "phone": phone, "password": d.PASSWORD,
                                                        "staff_role": role}, "owner")["user_id"]
        site.login(email, email, d.PASSWORD)
    monthly_costs(site, d, ids)
    say(f"{len(d.STAFF)} staff logins and monthly costs for six months")
    return ids


def existing(site, d) -> dict:
    """The ids of a demo business made earlier (to finish its later steps after a failure): matched by name / email."""
    site.login("owner", d.OWNER["email"], d.PASSWORD)
    s = site.get("/setup", "owner")
    by_name = lambda rows: {r["name"]: r["id"] for r in rows}
    places, items, sups = by_name(s["locations"]), by_name(s["items"]), by_name(s["suppliers"])
    users = {u.get("email"): u.get("id") or u.get("user_id") for u in s["users"]}
    for _, _, email in d.STAFF:
        site.login(email, email, d.PASSWORD)
    return {"tenant": s["business"]["id"], "place": {k: places[name] for k, name, *_ in d.PLACES},
            "item": {k: items[name] for k, name, *_ in d.ITEMS}, "supplier": {k: sups[name] for k, name, *_ in d.SUPPLIERS},
            "user": {email: users.get(email) for _, _, email in d.STAFF}}
