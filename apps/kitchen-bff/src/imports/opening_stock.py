# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Opening stock (stock-service ADJUST, the count set to what is on the shelf): one row per place and item. Each place's
rows go in as one adjustment with the note "Opening stock"."""
from __future__ import annotations

import grepx_contracts as gc

from .base import Column, Importer, Prepared, by_name, find


class OpeningStock(Importer):
    kind, title = "opening-stock", "Opening stock"
    notes = ("One row per place and item: how much is on the shelf now. The stock of that item at that place is set to it.",
             "Places and items must exist already. Export gives today's stock in the same layout.")
    columns = (Column("Place", "place", True, example="Central store - Andheri", help="a place's name"),
               Column("Item", "item", True, example="Basmati rice", help="an item's name"), Column("Qty", "qty", True, kind="number", example="120"))

    def context(self, k) -> dict:
        places, items = k.rows(gc.business.LOCATIONS), k.rows(gc.item.ITEMS)
        return {"places": by_name(places), "items": by_name(items), "place_names": {p["_key"]: p.get("name", "") for p in places},
                "item_names": {i["_key"]: (i.get("name", ""), i.get("unit", "")) for i in items}}

    def plan(self, rows, ctx):
        by_place: dict[str, Prepared] = {}
        for p in super().plan(rows, ctx):
            key = p.body.get("location_id") or f"?{p.rows[0]}"
            d = by_place.setdefault(key, Prepared([], p.label, action="update", body={"location_id": p.body.get("location_id"), "lines": []}))
            d.rows += p.rows
            d.errors += [f"row {p.rows[0]}: {e}" for e in p.errors]
            if p.body:
                d.body["lines"].append(p.body["line"])
        return list(by_place.values())

    def prepare(self, v, ctx):
        place, item = find(ctx["places"], v["place"], "place"), find(ctx["items"], v["item"], "item")
        return {"location_id": place["_key"], "line": {"item_id": item["_key"], "qty": v["qty"]}}, "update", place.get("name", "")

    def save(self, k, body):
        k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "ADJUST", "location_id": body["location_id"], "lines": body["lines"],
                                                    "note": "Opening stock (imported)"})

    def export(self, k, ctx):
        pn, it = ctx["place_names"], ctx["item_names"]
        rows = [[pn.get(l["location_id"], ""), it.get(l["item_id"], ("", ""))[0], l.get("qty")] for l in k.rows(gc.stock.STOCK_LEVELS)
                if l["item_id"] in it and l["location_id"] in pn]
        return sorted(rows, key=lambda r: (r[0].lower(), r[1].lower()))
