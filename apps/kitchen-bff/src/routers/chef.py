# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Chef: the recipe book (cards with method, cost per portion, allergens, veg marks), editing a card, today's prep list
by station, and the menu's allergen chart."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.errors import ApiError

from kitchen import Kitchen, allow
from views.chef import ALLERGENS, book, card

router = APIRouter(prefix="/chef", tags=["chef"])
KIT = "kitchen"
reader = allow("kitchen", "manage_business", module=KIT)


def recipes(k: Kitchen) -> dict:
    return {r["_key"]: r for r in k.rows(gc.item.RECIPES)}


@router.get("/recipes")
def recipe_book(k: Kitchen = Depends(reader)):
    cards = book(k.items(), recipes(k))
    return {"recipes": [{**c, "ingredients": len(c["ingredients"]), "steps": len(c["steps"] or [])} for c in cards], "allergens": ALLERGENS}


@router.get("/recipes/{item_id}")
def one(item_id: str, k: Kitchen = Depends(reader)):
    items = k.items()
    dish = items.get(item_id)
    if dish is None or dish.get("kind") != "finished":
        raise ApiError("UNKNOWN_ITEM", 404)
    return {"recipe": {**card(dish, recipes(k).get(item_id), items), "image_id": dish.get("image_id", "")}, "allergens": ALLERGENS}


@router.put("/recipes/{item_id}/card")
def save_card(item_id: str, body: dict, k: Kitchen = Depends(reader)):
    fields = {f: body.get(f) for f in ("steps", "station", "prep_min", "cook_min", "hold_hours", "yield_pct", "portion", "plating", "notes")}
    return k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_RECIPE_CARD", "item_id": item_id, **fields})


@router.get("/prep")
def prep(location_id: str, k: Kitchen = Depends(reader)):
    return k.cmd(gc.planning.REQUESTS, gc.planning.SERVICE, {"action": "PREP_LIST", "location_id": location_id})["plan"]


@router.get("/allergens")
def chart(k: Kitchen = Depends(reader)):
    return {"allergens": ALLERGENS, "dishes": [{"item_id": c["item_id"], "name": c["name"], "category": c["category"], "diet": c["diet"],
                                               "allergens": c["allergens"]} for c in book(k.items(), recipes(k))]}
