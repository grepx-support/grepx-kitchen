# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Recipes in bulk (item-service SAVE_RECIPE): one row per ingredient, rows of the same dish make its recipe. Importing
a dish again replaces its recipe."""
from __future__ import annotations

import grepx_contracts as gc

from .base import Column, Importer, Prepared, by_name, find


class Recipes(Importer):
    kind, title = "recipes", "Recipes"
    notes = ("One row per ingredient. All rows with the same Dish make that dish's recipe; Batch output is how much one batch makes.",
             "Dish and ingredients must be items already (import items first). Importing a dish again replaces its recipe.")
    columns = (Column("Dish", "dish", True, example="Chicken biryani", help="an item you make (finished)"),
               Column("Batch output", "batch_output", True, kind="number", example="20", help="portions (in the dish's unit) one batch makes"),
               Column("Ingredient", "ingredient", True, example="Basmati rice", help="an item's name"),
               Column("Qty", "qty", True, kind="number", example="2.5", help="how much of the ingredient one batch uses, in its unit"))

    def context(self, k) -> dict:
        items = k.rows(gc.item.ITEMS)
        return {"items": by_name(items), "names": {i["_key"]: i.get("name", "") for i in items}, "recipes": {r["_key"]: r for r in k.rows(gc.item.RECIPES)}}

    def plan(self, rows, ctx):
        lines = super().plan(rows, ctx)
        dishes: dict[str, Prepared] = {}
        for p in lines:
            key = p.label.lower()
            d = dishes.setdefault(key, Prepared([], p.label, body={"ingredients": []}))
            d.rows += p.rows
            d.errors += [f"row {p.rows[0]}: {e}" for e in p.errors]
            if p.body:
                if d.body.get("batch_output") not in (None, p.body["batch_output"]):
                    d.errors.append(f"row {p.rows[0]}: Batch output differs from the dish's first row")
                d.body |= {"item_id": p.body["item_id"], "batch_output": p.body["batch_output"]}
                d.body["ingredients"].append(p.body["line"])
                d.action = p.action
        return list(dishes.values())

    def prepare(self, v, ctx):
        dish, part = find(ctx["items"], v["dish"], "item"), find(ctx["items"], v["ingredient"], "item")
        if v["qty"] <= 0 or v["batch_output"] <= 0:
            raise ValueError("Qty and Batch output must be above zero")
        return ({"item_id": dish["_key"], "batch_output": v["batch_output"], "line": {"item_id": part["_key"], "qty": v["qty"]}},
                "update" if dish["_key"] in ctx["recipes"] else "create", dish.get("name", v["dish"]))

    def save(self, k, body):
        k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_RECIPE", **body})

    def export(self, k, ctx):
        names = ctx["names"]
        return [[names.get(r["_key"], ""), r.get("batch_output"), names.get(l["item_id"], ""), l["qty"]]
                for r in sorted(ctx["recipes"].values(), key=lambda r: names.get(r["_key"], "").lower()) for l in r.get("ingredients") or []]
