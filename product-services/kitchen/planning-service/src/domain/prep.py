# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Today's prep list for a kitchen, by station: what is still to make this week, spread over the days left (today
included), rounded up to whole batches; with each dish's minutes so the station knows when to start.

The week's target already takes away what is on hand, so as cooks record batches the list shrinks by itself."""
from __future__ import annotations

import math

UNASSIGNED = "no station yet"


def today_qty(target: float, days_left: int, batch_output: float | None) -> tuple[float, int | None]:
    share = max(0.0, target) / max(1, days_left)
    if not batch_output or batch_output <= 0:
        return math.ceil(share), None
    batches = math.ceil(share / batch_output) if share > 0 else 0
    return batches * batch_output, batches


def prep_list(lines: list[dict], recipes: dict, days_left: int, made_today: dict[str, float]) -> dict:
    stations: dict[str, list] = {}
    for line in lines:
        if not line.get("target") or line["target"] <= 0:
            continue
        recipe = recipes.get(line["item_id"]) or {}
        qty, batches = today_qty(float(line["target"]), days_left, recipe.get("batch_output"))
        if qty <= 0:
            continue
        minutes = int(recipe.get("prep_min") or 0) + int(recipe.get("cook_min") or 0)   # one run; batches cook side by side
        stations.setdefault(recipe.get("station") or UNASSIGNED, []).append({
            "item_id": line["item_id"], "name": line.get("name", ""), "unit": line.get("unit", ""), "qty": qty, "batches": batches,
            "made_today": made_today.get(line["item_id"], 0), "week_left": line["target"], "minutes": minutes,
            "prep_min": recipe.get("prep_min") or 0, "cook_min": recipe.get("cook_min") or 0, "has_card": bool(recipe.get("steps"))})
    out = [{"station": name, "tasks": sorted(tasks, key=lambda t: -t["minutes"]), "minutes": sum(t["minutes"] for t in tasks)}
           for name, tasks in stations.items()]
    return {"stations": sorted(out, key=lambda s: (s["station"] == UNASSIGNED, -s["minutes"])), "days_left": days_left}
