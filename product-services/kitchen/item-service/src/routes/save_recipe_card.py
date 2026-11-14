# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_RECIPE_CARD - the chef's card of a dish: method steps, station, prep and cook minutes, yield after trim,
portion, plating, holding time, photo. Kept on the recipe row beside the ingredients (SAVE_RECIPE leaves it alone)."""
from grepx_service import RequestContext

from domain import clean_card
from dto import ItemKind, ReasonCode, Table
from .common import guard, mine

FIELDS = ("steps", "station", "prep_min", "cook_min", "hold_hours", "yield_pct", "portion", "plating", "photo_id", "notes")


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    item_id = ctx.text("item_id")
    product = mine(ctx, Table.ITEMS.value, item_id, tenant)
    if product is None:
        return ctx.reject(ReasonCode.UNKNOWN_ITEM)
    if product.get("kind") != ItemKind.FINISHED.value:
        return ctx.reject(ReasonCode.NOT_FINISHED_GOOD)
    try:
        card = clean_card({k: ctx.get(k) for k in FIELDS})
    except ValueError as exc:
        return ctx.reject(str(exc))
    recipe = ctx.read.accepted_one(Table.RECIPES.value, item_id) or {"item_id": item_id, "tenant_id": tenant, "batch_output": 1, "ingredients": []}
    full = {**{k: v for k, v in recipe.items() if not k.startswith("_") and k not in ("status",)}, **card, "tenant_id": tenant}
    ctx.emitter.submit(Table.RECIPES.value, item_id, "ACCEPTED", full)
    ctx.accept({"recipe": full})
