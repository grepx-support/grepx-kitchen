# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The chef's side of a dish: the recipe card (method, station, times, yield, plating, holding time), the allergens
and veg / egg / non-veg mark of ingredients, and what a dish carries from its ingredients."""
from __future__ import annotations

# The 14 allergens food law asks for (EU / UK / FSANZ list) plus sesame-free markets' "peanut" kept apart from nuts.
ALLERGENS = ("gluten", "crustaceans", "eggs", "fish", "peanuts", "soy", "milk", "tree_nuts", "celery", "mustard", "sesame",
             "sulphites", "lupin", "molluscs")
DIETS = ("veg", "egg", "non_veg", "vegan")               # Indian menus mark veg / egg / non-veg; vegan is veg without milk or eggs
RANK = {"vegan": 0, "veg": 1, "egg": 2, "non_veg": 3}     # a dish is as "non-veg" as its most non-veg ingredient
STATIONS = ("prep", "tandoor", "curry", "grill", "fry", "rice", "bakery", "cold", "dessert", "pack")


def allergens(value) -> list[str]:
    got = {str(a).strip().lower().replace(" ", "_") for a in (value or [])}
    if got - set(ALLERGENS):
        raise ValueError("INVALID_ALLERGEN")
    return [a for a in ALLERGENS if a in got]


def diet(value) -> str:
    value = str(value or "").strip().lower().replace("-", "_")
    if value and value not in DIETS:
        raise ValueError("INVALID_DIET")
    return value


def _minutes(value, most: int, reason: str) -> int:
    try:
        n = int(float(value or 0))
    except (TypeError, ValueError):
        raise ValueError(reason)
    if not 0 <= n <= most:
        raise ValueError(reason)
    return n


def clean_card(raw: dict) -> dict:
    steps = [" ".join(str(s).split())[:400] for s in raw.get("steps") or [] if str(s).strip()]
    if len(steps) > 40:
        raise ValueError("TOO_MANY_STEPS")
    station = " ".join(str(raw.get("station") or "").split()).lower()[:30]
    try:
        yield_pct = float(100 if raw.get("yield_pct") in (None, "") else raw["yield_pct"])
    except (TypeError, ValueError):
        raise ValueError("INVALID_YIELD")
    if not 1 <= yield_pct <= 100:
        raise ValueError("INVALID_YIELD")
    return {"steps": steps, "station": station, "prep_min": _minutes(raw.get("prep_min"), 1440, "INVALID_TIME"),
            "cook_min": _minutes(raw.get("cook_min"), 1440, "INVALID_TIME"), "hold_hours": _minutes(raw.get("hold_hours"), 168, "INVALID_TIME"),
            "yield_pct": round(yield_pct, 1), "portion": " ".join(str(raw.get("portion") or "").split())[:60],
            "plating": str(raw.get("plating") or "").strip()[:800], "photo_id": str(raw.get("photo_id") or "")[:64],
            "notes": str(raw.get("notes") or "").strip()[:800]}


def dish_marks(lines: list[dict], items: dict[str, dict]) -> dict:
    """What a dish carries from its ingredients: every allergen of any ingredient; the most non-veg mark (unmarked
    ingredients make the mark unknown, so it is never shown as veg by mistake)."""
    found, marks = set(), []
    for line in lines:
        item = items.get(line["item_id"]) or {}
        found.update(item.get("allergens") or [])
        marks.append(item.get("diet") or "")
    mark = "" if not marks or "" in marks else max(marks, key=RANK.get)
    return {"allergens": [a for a in ALLERGENS if a in found], "diet": mark}
