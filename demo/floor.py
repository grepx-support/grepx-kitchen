# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 4 - the warehouse floor and inventory control: bins with the lots filed in them, a delivery of cream that
expires tomorrow, some waste with its reasons, minimum / maximum levels (so some alerts show), a pick list waiting for the truck, a delivery run
planned for the Bondi trip, and one purchase order sent to its supplier (logged in the outbox while in test mode)."""
from __future__ import annotations

from datetime import date, timedelta

from catering import held
from setup import staff


def run(site, d, ids: dict, say) -> None:
    p, item, wes = ids["place"], ids["item"], staff(d, "warehouse")[1]
    have = {b["code"]: b["id"] for b in site.get(f"/warehouse?location_id={p['wh']}", wes)["bins"]}   # made before (a resumed run)
    bins = {code: have.get(code) or site.post("/warehouse/bins", {"location_id": p["wh"], "code": code, "zone": zone}, "owner")["bin_id"]
            for code, zone in d.BINS}
    floor = site.get(f"/warehouse?location_id={p['wh']}", wes)
    keys = {v: k for k, v in item.items()}
    for lot in floor["lots"]:
        code = d.BIN_OF.get(keys.get(lot["item_id"], ""))
        if code:
            site.post(f"/warehouse/lots/{lot['lot_id']}/move", {"bin_id": bins[code]}, wes)
    expires = lambda days: (date.today() + timedelta(days=days)).isoformat() if days is not None else ""
    site.post("/stock/receive", {"location_id": p["wh"], "note": "Market run", "lines": [
        {"item_id": item[k], "qty": q, "expiry": expires(days), "lot_code": lot, "bin_id": bins[b]} for k, q, days, lot, b in d.MARKET]}, wes)
    say(f"{len(bins)} bins, {len(floor['lots'])} lots filed, a market delivery that expires tomorrow")
    have = held(site, ids, "wh", wes)
    for key, qty, why in d.WASTE:                                # at the store, never more than it holds
        qty = min(qty, max(0, have.get(item[key], 0)))
        if qty > 0:
            site.post("/stock/waste", {"location_id": p["wh"], "reason": why, "lines": [{"item_id": item[key], "qty": qty}]}, wes)
    say("some waste at the central store, with reasons")
    for key, (low, high) in d.PAR.items():
        site.post("/inventory/par", {"location_id": p["wh"], "item_id": item[key], "min": low, "max": high}, "owner")
    site.post("/inventory/alerts/check", {}, "owner")
    say(f"minimum / maximum for {len(d.PAR)} items; alerts checked")
    site.post("/warehouse/picks", {"from_location_id": p["wh"], "to_location_id": p[d.SELLERS[-1]],
                                   "lines": [{"item_id": item[k], "qty": q} for k, q in d.PICK]}, wes)
    waiting = [t for t in site.get("/runs", wes)["waiting"] if t["date"] == date.today().isoformat()][:6]   # today's trips
    drivers = {d["name"]: d["id"] for d in site.get("/runs", wes)["drivers"]}
    if waiting:
        site.post("/runs", {"date": date.today().isoformat(), **d.RUN,
                            "driver_id": drivers.get(staff(d, "delivery")[0], ""), "drive_minutes": 25, "service_minutes": 10,
                            "delivery_ids": [t["id"] for t in waiting]}, wes)
    say(f"a pick list for the {next(n for k, n, *_ in d.PLACES if k == d.SELLERS[-1])}; a delivery run with {len(waiting)} stops for {staff(d, 'delivery')[0]}")
    open_orders = site.get("/orders?state=saved", "owner")["orders"]
    if open_orders:
        site.post(f"/orders/{open_orders[0]['id']}/send", {"channels": ["email", "whatsapp"]}, "owner")
        say(f"{open_orders[0]['number']} sent to {open_orders[0]['supplier_name']} (see Outbox)")
