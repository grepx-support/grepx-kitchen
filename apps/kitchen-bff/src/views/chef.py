# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The recipe book as the chef reads it: each dish's card joined with its ingredients' names, costs, allergens and
veg marks. The marks follow item-service's rule (domain/chef.py dish_marks): every allergen of any ingredient; the most
non-veg ingredient decides; an unmarked ingredient leaves the mark unknown."""

ALLERGENS = ("gluten", "crustaceans", "eggs", "fish", "peanuts", "soy", "milk", "tree_nuts", "celery", "mustard", "sesame",
             "sulphites", "lupin", "molluscs")
RANK = {"vegan": 0, "veg": 1, "egg": 2, "non_veg": 3}
CARD = ("steps", "station", "prep_min", "cook_min", "hold_hours", "yield_pct", "portion", "plating", "notes", "photo_id")


def marks(lines: list[dict], items: dict) -> dict:
    found, diets = set(), []
    for line in lines:
        item = items.get(line["item_id"]) or {}
        found.update(item.get("allergens") or [])
        diets.append(item.get("diet") or "")
    return {"allergens": [a for a in ALLERGENS if a in found], "diet": "" if not diets or "" in diets else max(diets, key=RANK.get)}


def costs(recipe: dict, items: dict) -> tuple[list[dict], float | None]:
    """The ingredient lines of one batch with their cost, and the cost of one unit made (after the trim / cooking loss)."""
    lines, total = [], 0.0
    for line in recipe.get("ingredients") or []:
        item = items.get(line["item_id"]) or {}
        cost = float(line["qty"]) * float(item.get("cost") or 0)
        total += cost
        lines.append({"item_id": line["item_id"], "name": item.get("name", "?"), "unit": item.get("unit", ""), "qty": line["qty"],
                      "cost": round(cost, 2), "allergens": item.get("allergens") or [], "diet": item.get("diet") or ""})
    out = float(recipe.get("batch_output") or 0) * float(recipe.get("yield_pct") or 100) / 100
    return lines, (round(total / out, 2) if out > 0 and lines else None)


def card(dish: dict, recipe: dict | None, items: dict) -> dict:
    recipe = recipe or {}
    lines, unit_cost = costs(recipe, items)
    price = float(dish.get("price") or 0)
    return {"item_id": dish["_key"], "name": dish.get("name", ""), "unit": dish.get("unit", ""), "category": dish.get("category", ""),
            "price": price, "unit_cost": unit_cost, "margin_pct": round((price - unit_cost) / price * 100, 1) if price and unit_cost is not None else None,
            "batch_output": recipe.get("batch_output"), "ingredients": lines, **marks(recipe.get("ingredients") or [], items),
            **{k: recipe.get(k) for k in CARD}, "has_card": bool(recipe.get("steps"))}


def book(items: dict, recipes: dict) -> list[dict]:
    dishes = [i for i in items.values() if i.get("kind") == "finished" and i.get("active", True)]
    return sorted((card(d, recipes.get(d["_key"]), items) for d in dishes), key=lambda c: c["name"].lower())
