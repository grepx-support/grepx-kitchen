# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PRODUCTION_TARGET - this week's target for a kitchen: finished goods, batches, ingredients to buy (R5, KIT-03..05)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import production_target, week_start
from dto import PlanKind, ReasonCode, Table
from .common import Stop, run, total


def target(ctx: RequestContext, view) -> tuple[dict, dict]:
    """This week's target at the view's kitchen, and the recipes it used (PREP_LIST uses both)."""
    kitchen = view.location()
    if kitchen.get("kind") != gc.business.LocationKind.KITCHEN.value:
        raise Stop(ReasonCode.NOT_A_KITCHEN)
    week = week_start(view.today()).isoformat()
    manual = (ctx.read.accepted_one(Table.PLANS.value, f"{PlanKind.TARGET.value}:{view.tenant}:{week}") or {}).get("items") or {}
    stock = view.stock()
    holding = {l["_key"] for l in view.locations() if l.get("holding")} | {kitchen["_key"]}
    recipes = {r["_key"]: r for r in ctx.read.accepted(gc.item.RECIPES, tenant_id=view.tenant)}
    names = {i["_key"]: i for i in view.items()}
    result = production_target(view.items(gc.item.ItemKind.FINISHED.value), recipes, view.usage(), total(stock), view.safety(),
                               manual, total(stock, holding), names)
    return {**result, "week": week, "location_id": kitchen["_key"]}, recipes


def handle(ctx: RequestContext) -> None:
    def body(view):
        return target(ctx, view)[0]
    run(ctx, body)
