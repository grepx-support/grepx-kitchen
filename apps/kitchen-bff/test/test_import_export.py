# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bulk import / export: templates, a file with mistakes checked row by row (nothing saved), imported, imported again
(updates, no duplicates), then everything exported - suppliers, items, recipes, opening stock, employees."""
import base64

from grepx_bff.tabular import read, write_csv, write_xlsx

from kitchen_stack import env, ok, open_business  # noqa: F401


def upload(api, owner, kind, heads, rows, step="check", xlsx=False):
    data = write_xlsx(heads, rows) if xlsx else write_csv(heads, rows)
    body = {"name": f"{kind}.{'xlsx' if xlsx else 'csv'}", "file": "data:;base64," + base64.b64encode(data).decode()}
    return api.post(f"/api/v1/data/{kind}/{step}", headers=owner, json=body)


def test_bulk_import_and_export(env):
    stack, api = env
    owner = open_business(api, "Bulk Kitchen", "owner@bulk.sg")["owner"]
    for name, kind in (("Central store", "warehouse"), ("Kitchen", "kitchen")):
        ok(api.post("/api/v1/setup/locations", headers=owner, json={"name": name, "kind": kind}))
    assert {k["kind"] for k in ok(api.get("/api/v1/data", headers=owner))["kinds"]} == {"suppliers", "items", "recipes", "opening-stock", "employees"}
    tpl = api.get("/api/v1/data/items/template", headers=owner)
    assert tpl.status_code == 200 and read(tpl.content, "t.xlsx").headings[:3] == ["Name *", "Kind *", "Unit *"]
    # --- suppliers, then items with one bad row (checked first: nothing saved) ---
    assert ok(upload(api, owner, "suppliers", ["Name", "Email"], [["Fresh Farms", "orders@ff.test"], ["Spice Hub", ""]], "import"))["creates"] == 2
    heads = ["Name", "Kind", "Unit", "Unit cost", "Supplier", "Allergens"]
    rows = [["Basmati rice", "ingredient", "kg", "92.5", "Fresh Farms", ""], ["Chicken", "ingredient", "kg", "260", "Fresh Farms", ""],
            ["Ghee", "ingredient", "kg", "abc", "Nobody & Co", "milk"], ["Chicken biryani", "finished", "portion", "", "", "milk"]]
    check = ok(upload(api, owner, "items", heads, rows, xlsx=True))
    assert (check["saved"], check["ok"], check["failed"]) == (False, 3, 1)
    bad = next(r for r in check["rows"] if r["errors"])
    assert bad["rows"] == [4] and any("number" in e for e in bad["errors"])
    assert ok(api.get("/api/v1/setup", headers=owner))["items"] == []                      # nothing saved by a check
    done = ok(upload(api, owner, "items", heads, rows, "import", xlsx=True))
    assert (done["saved"], done["creates"], done["failed"]) == (True, 3, 1)
    again = ok(upload(api, owner, "items", heads, [["Basmati rice", "ingredient", "kg", "95", "Fresh Farms", ""]], "import"))
    items = ok(api.get("/api/v1/setup", headers=owner))["items"]
    assert again["updates"] == 1 and len(items) == 3 and next(i for i in items if i["name"] == "Basmati rice")["cost"] == 95
    assert upload(api, owner, "items", ["Title"], [["x"]]).json()["detail"]["reason"] == "MISSING_COLUMNS"
    # --- a recipe from several rows; opening stock per place; employees ---
    rec = ok(upload(api, owner, "recipes", ["Dish", "Batch output", "Ingredient", "Qty"],
                    [["Chicken biryani", "20", "Basmati rice", "2.5"], ["Chicken biryani", "20", "Chicken", "3"]], "import"))
    assert (rec["total"], rec["ok"], rec["rows"][0]["rows"]) == (1, 1, [2, 3])
    stock = ok(upload(api, owner, "opening-stock", ["Place", "Item", "Qty"], [["Central store", "Basmati rice", "120"], ["Central store", "Chicken", "40"],
                                                                          ["Kitchen", "Chicken", "5"], ["Moon base", "Chicken", "1"]], "import"))
    assert (stock["ok"], stock["failed"]) == (2, 1)
    team = ok(upload(api, owner, "employees", ["Name", "Email", "Home site", "Pay basis", "Pay rate"],
                     [["Meera Iyer", "meera@bulk.test", "Kitchen", "monthly", "28000"], ["Ravi", "", "Central store", "weekly", "1"]], "import"))
    assert (team["ok"], team["failed"]) == (1, 1)
    # --- everything back out ---
    out = read(api.get("/api/v1/data/recipes/export?format=csv", headers=owner).content, "r.csv")
    assert [(r["dish"], r["ingredient"], r["qty"]) for r in out.rows] == [("Chicken biryani", "Basmati rice", "2.5"), ("Chicken biryani", "Chicken", "3")]
    levels = read(api.get("/api/v1/data/opening-stock/export", headers=owner).content, "s.xlsx")
    assert {(r["place"], r["item"], r["qty"]) for r in levels.rows} >= {("Central store", "Basmati rice", "120"), ("Kitchen", "Chicken", "5")}
    people = read(api.get("/api/v1/data/employees/export?format=csv", headers=owner).content, "e.csv")
    assert people.rows[0]["home site"] == "Kitchen" and people.rows[0]["pay rate"] == "28000"
