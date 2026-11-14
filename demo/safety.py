# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Demo food safety: the standard checks at the kitchen and the first outlet, this morning's readings (one warm
fridge, with the action taken) and the opening checklist; the rest is left due so the page shows what to do."""
from __future__ import annotations


def run(site, d, ids: dict, say) -> None:
    places = [ids["place"][k] for k, _, kind, *_ in d.PLACES if kind == "kitchen"] + [ids["place"][d.SELLERS[0]]]
    for place in places:
        site.post("/safety/presets", {"site_id": place}, "owner")
    checks = {p["name"]: p for p in site.get(f"/safety/day?site_id={places[0]}", "owner")["points"]}
    readings = [("Walk-in fridge", 3.5, ""), ("Freezer", -20, ""), ("Hot holding (bain-marie)", 58, "Reheated to 75°C, bain-marie turned up")]
    for name, value, action in readings:
        site.post("/safety/record", {"point_id": checks[name]["point_id"], "value": value, "action_taken": action}, "owner")
    opening = checks["Opening checks"]
    site.post("/safety/record", {"point_id": opening["point_id"], "answers": {i: True for i in opening["questions"]}}, "owner")
    say(f"food safety checks at {len(places)} places, this morning's readings (one out of range)")
