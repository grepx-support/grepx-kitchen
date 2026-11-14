# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Items and suppliers in bulk (item-service SAVE_ITEM / SAVE_SUPPLIER), matched by name."""
from __future__ import annotations

import grepx_contracts as gc

from .base import Column, Importer, by_name, find

KINDS = [k.value for k in gc.item.ItemKind]


class Suppliers(Importer):
    kind, title = "suppliers", "Suppliers"
    notes = ("One row per supplier. A supplier already there with the same name is updated.",)
    columns = (Column("Name", "name", True, example="Fresh Farms Co", help="the supplier's name (matched to update)"),
               Column("Contact", "contact", example="Ravi"), Column("Phone", "phone", example="+919800000123"),
               Column("Email", "email", example="orders@freshfarms.test", help="purchase orders are emailed here"), Column("Notes", "notes"))

    def context(self, k) -> dict:
        return {"suppliers": by_name(k.rows(gc.item.SUPPLIERS))}

    def prepare(self, v, ctx):
        old = ctx["suppliers"].get(v["name"].lower())
        body = {**{c.key: v[c.key] for c in self.columns if v[c.key] is not None}, **({"supplier_id": old["_key"]} if old else {})}
        return body, "update" if old else "create", v["name"]

    def save(self, k, body):
        k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_SUPPLIER", **body})

    def export(self, k, ctx):
        return [[s.get("name"), s.get("contact"), s.get("phone"), s.get("email"), s.get("notes")] for s in sorted(k.rows(gc.item.SUPPLIERS), key=lambda s: s.get("name", "").lower())]


class Items(Importer):
    kind, title = "items", "Items"
    notes = ("One row per item: what you buy (ingredient), make and sell (finished) or use up (supply - boxes, gloves).",
             "The supplier must already exist (import suppliers first). An item already there with the same name is updated.")
    columns = (Column("Name", "name", True, example="Basmati rice", help="matched to update"),
               Column("Kind", "kind", True, example="ingredient", help=" / ".join(KINDS)),
               Column("Unit", "unit", True, example="kg", help="kg, l, each, box..."),
               Column("Unit cost", "cost", kind="number", example="92.5", help="what one unit costs you"),
               Column("Sale price", "price", kind="number", example="", help="for finished items you invoice"),
               Column("Supplier", "supplier", example="Fresh Farms Co", help="a supplier's name"),
               Column("Category", "category", example="Dry goods"), Column("Shelf life days", "shelf_life_days", kind="int", example="365"),
               Column("Barcode", "barcode"), Column("Allergens", "allergens", kind="list", example="", help="comma separated: gluten, milk, eggs, peanuts..."),
               Column("Diet", "diet", example="veg", help="veg / egg / non_veg / vegan"))

    def context(self, k) -> dict:
        sup = k.rows(gc.item.SUPPLIERS)
        return {"items": by_name(k.rows(gc.item.ITEMS)), "suppliers": by_name(sup), "supplier_names": {s["_key"]: s.get("name", "") for s in sup}}

    def prepare(self, v, ctx):
        if v["kind"].lower() not in KINDS:
            raise ValueError(f"Kind must be one of {', '.join(KINDS)}")
        supplier = find(ctx["suppliers"], v["supplier"], "supplier")
        old = ctx["items"].get(v["name"].lower())
        body = {k: v[k] for k in ("name", "unit", "cost", "price", "category", "shelf_life_days", "barcode", "allergens", "diet") if v[k] is not None}
        body |= {"kind": v["kind"].lower(), **({"supplier_id": supplier["_key"]} if supplier else {}), **({"item_id": old["_key"]} if old else {})}
        return body, "update" if old else "create", v["name"]

    def save(self, k, body):
        k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_ITEM", **body})

    def export(self, k, ctx):
        names = ctx["supplier_names"]
        return [[i.get("name"), i.get("kind"), i.get("unit"), i.get("cost"), i.get("price") or "", names.get(i.get("supplier_id"), ""), i.get("category"),
                 i.get("shelf_life_days") or "", i.get("barcode"), ", ".join(i.get("allergens") or []), i.get("diet")]
                for i in sorted(k.rows(gc.item.ITEMS), key=lambda i: (i.get("kind", ""), i.get("name", "").lower()))]
