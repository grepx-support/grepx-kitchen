# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 4 - the warehouse floor and inventory control: bins with the lots filed in them, a delivery of cream that
expires tomorrow, some waste with its reasons, minimum / maximum levels (so some alerts show), a pick list waiting for the truck, a delivery run
planned for the Bondi trip, and one purchase order sent to its supplier (logged in the outbox while in test mode)."""
from __future__ import annotations

from datetime import date, timedelta

import data


def run(site, ids: dict, say) -> None:
    p, item, wes = ids["place"], ids["item"], "wes@demo-taco.test"
    bins = {code: site.post("/warehouse/bins", {"location_id": p["wh"], "code": code, "zone": zone}, "owner")["bin_id"] for code, zone in data.BINS}
    floor = site.get(f"/warehouse?location_id={p['wh']}", wes)
    keys = {v: k for k, v in item.items()}
    for lot in floor["lots"]:
        code = data.BIN_OF.get(keys.get(lot["item_id"], ""))
        if code:
            site.post(f"/warehouse/lots/{lot['lot_id']}/move", {"bin_id": bins[code]}, wes)
    soon = (date.today() + timedelta(days=1)).isoformat()
    site.post("/stock/receive", {"location_id": p["wh"], "note": "Market run", "lines": [
        {"item_id": item["coriander"], "qty": 6, "expiry": soon, "lot_code": "MKT-1", "bin_id": bins["C-02"]},
        {"item_id": item["cheese"], "qty": 4, "lot_code": "OX-2207", "bin_id": bins["C-02"]}]}, wes)
    say(f"{len(bins)} bins, {len(floor['lots'])} lots filed, a market delivery that expires tomorrow")
    for key, qty, why in (("coriander", 2, "spoiled"), ("tortilla", 1, "damaged"), ("birria", 3, "overproduced")):
        site.post("/stock/waste", {"location_id": p["kit"], "reason": why, "lines": [{"item_id": item[key], "qty": qty}]}, "kim@demo-taco.test")
    say("some waste in the kitchen, with reasons")
    for key, (low, high) in data.PAR.items():
        site.post("/inventory/par", {"location_id": p["wh"], "item_id": item[key], "min": low, "max": high}, "owner")
    site.post("/inventory/alerts/check", {}, "owner")
    say(f"minimum / maximum for {len(data.PAR)} items; alerts checked")
    site.post("/warehouse/picks", {"from_location_id": p["wh"], "to_location_id": p["truck"], "lines": [
        {"item_id": item["tortilla"], "qty": 6}, {"item_id": item["box"], "qty": 4}, {"item_id": item["coriander"], "qty": 3}]}, wes)
    waiting = [t for t in site.get("/runs", wes)["waiting"] if t["date"] == date.today().isoformat()][:6]   # today's trips
    drivers = {d["name"]: d["id"] for d in site.get("/runs", wes)["drivers"]}
    if waiting:
        site.post("/runs", {"date": date.today().isoformat(), "start_time": "10:30", "name": "Eastern suburbs", "vehicle": "Van 1",
                            "driver_id": drivers.get("Dan Driver", ""), "drive_minutes": 25, "service_minutes": 10,
                            "delivery_ids": [t["id"] for t in waiting]}, wes)
    say(f"a pick list for the food truck; a delivery run with {len(waiting)} stops for Dan")
    open_orders = site.get("/orders?state=saved", "owner")["orders"]
    if open_orders:
        site.post(f"/orders/{open_orders[0]['id']}/send", {"channels": ["email", "whatsapp"]}, "owner")
        say(f"{open_orders[0]['number']} sent to {open_orders[0]['supplier_name']} (see Outbox)")
