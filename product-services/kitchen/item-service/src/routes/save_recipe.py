# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_RECIPE - output of one batch of a finished product, and optionally its ingredients (KIT-02)."""
from grepx_service import RequestContext

from domain import clean_recipe
from dto import ItemKind, ReasonCode, Table
from .common import guard, mine


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
        row = clean_recipe({"batch_output": ctx.get("batch_output"), "ingredients": ctx.get("ingredients") or []})
    except ValueError as exc:
        return ctx.reject(str(exc))
    for line in row["ingredients"]:
        ingredient = mine(ctx, Table.ITEMS.value, line["item_id"], tenant)
        if ingredient is None or ingredient.get("kind") == ItemKind.FINISHED.value or line["item_id"] == item_id:
            return ctx.reject(ReasonCode.UNKNOWN_ITEM, line["item_id"])
    card = {k: v for k, v in (ctx.read.accepted_one(Table.RECIPES.value, item_id) or {}).items()
            if k not in ("batch_output", "ingredients", "status") and not k.startswith("_")}   # the chef's card stays
    full = {**card, "item_id": item_id, "tenant_id": tenant, **row}
    ctx.emitter.submit(Table.RECIPES.value, item_id, "ACCEPTED", full)
    ctx.accept({"recipe": full})
