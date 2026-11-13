# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Cooking for catering orders, the way the kitchen would: the ingredients go from the central store to the kitchen,
are used, and the batches are made there - so a catering invoice issued from the kitchen has food to take."""
from __future__ import annotations

from history import cook
from setup import staff


def held(site, ids, place: str, who: str) -> dict[str, float]:
    """item id -> quantity at one place right now."""
    return {l["item_id"]: l["qty"] for l in site.get("/stock", who)["levels"] if l["location_id"] == ids["place"][place]}


def cook_for(site, d, ids, needed: dict[str, float]) -> None:
    """needed: {product key: qty}; whole batches are made, so a little may be left over."""
    made, used = cook(d, {k: q for k, q in needed.items() if k in d.RECIPES})
    if not made:
        return
    p, wes, kim = ids["place"], staff(d, "warehouse")[1], staff(d, "kitchen")[1]
    lines = lambda qty: [{"item_id": ids["item"][k], "qty": round(q, 2)} for k, q in qty.items() if q > 0]
    have = held(site, ids, "wh", wes)
    short = {k: q - max(0.0, have.get(ids["item"][k], 0)) for k, q in used.items()}
    if any(q > 0 for q in short.values()):                       # a top-up delivery for what the store lacks
        site.post("/stock/receive", {"location_id": p["wh"], "note": "Top-up for catering", "lines": lines({k: q + 0.5 for k, q in short.items() if q > 0})}, wes)
    site.post("/stock/send", {"from_location_id": p["wh"], "to_location_id": p["kit"], "lines": lines(used)}, wes)
    site.post("/kitchen/use", {"location_id": p["kit"], "lines": lines(used)}, kim)
    site.post("/kitchen/production", {"location_id": p["kit"], "lines": lines(made)}, kim)
