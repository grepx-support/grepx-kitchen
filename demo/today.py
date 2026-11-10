# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 3 - today, half done, so every board has something on it: an order on its way and one received, a delivery
on the road and one arrived, part of the cooking recorded - and no closing yet (try it as Tia)."""
from __future__ import annotations

import data


def run(site, ids: dict, say) -> None:
    p, wes, kim, dan = ids["place"], "wes@demo-taco.test", "kim@demo-taco.test", "dan@demo-taco.test"
    rec = site.get(f"/orders/recommendation?location_id={p['wh']}", wes)
    by_supplier: dict = {}
    for line in rec["lines"]:
        if line.get("supplier_id") and line.get("recommended"):
            by_supplier.setdefault(line["supplier_id"], []).append({"item_id": line["item_id"], "qty": line["recommended"]})
    orders = [site.post("/orders", {"supplier_id": sup, "location_id": p["wh"], "lines": lines}, wes) for sup, lines in by_supplier.items()]
    if orders:                                                   # one arrived already, the others are on order
        first = site.get(f"/orders/{orders[0]['po_id']}", wes)
        site.post(f"/orders/{first['id']}/receive", {"lines": [{"item_id": l["item_id"], "qty": l["qty"]} for l in first["lines"]]}, wes)
    say(f"{len(orders)} purchase orders from the recommendation, 1 received")
    target = site.get(f"/kitchen/target?location_id={p['kit']}", kim)
    made = [{"item_id": l["item_id"], "qty": l["batch_output"]} for l in target["lines"] if l.get("batch_output")]
    output = {ids["item"][k]: v[0] for k, v in data.RECIPES.items()}
    used = {}
    for line in made:
        product = next(k for k, v in ids["item"].items() if v == line["item_id"])
        for k, q in data.RECIPES[product][1].items():
            used[ids["item"][k]] = used.get(ids["item"][k], 0) + q * line["qty"] / output[line["item_id"]]
    if used:
        site.post("/kitchen/use", {"location_id": p["kit"], "lines": [{"item_id": i, "qty": round(q, 2)} for i, q in used.items()]}, kim)
    if made:
        site.post("/kitchen/production", {"location_id": p["kit"], "lines": made}, kim)
    say(f"kitchen: one batch of each product recorded against this week's target")
    for place in ("bondi", "parra"):
        plan = site.get(f"/stock/warehouse-out?to_location_id={p[place]}", wes)
        lines = [{"item_id": l["item_id"], "qty": l["suggested"]} for l in plan["lines"] if l.get("suggested")]
        if lines:
            site.post("/stock/send", {"from_location_id": p["wh"], "to_location_id": p[place], "lines": lines}, wes)
    trips = site.get("/stock/deliveries", dan)["deliveries"]
    arrived = next((t for t in trips if t["to"] == "Parramatta store" and t["state"] == "sent"), None)
    if arrived:
        site.post(f"/stock/deliveries/{arrived['id']}/delivered", {}, dan)
    say("deliveries: Bondi on the way, Parramatta delivered")
