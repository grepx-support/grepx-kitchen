# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PREP_LIST - today's prep list for a kitchen, by station (domain/prep.py), with what was made there today."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import prep_list, week_start
from .common import run
from .production_target import target


def handle(ctx: RequestContext) -> None:
    def body(view):
        plan, recipes = target(ctx, view)
        today = view.today()
        days_left = 7 - (today - week_start(today)).days
        made = {}
        for m in ctx.read.accepted(gc.stock.STOCK_MOVEMENTS, tenant_id=view.tenant, location_id=plan["location_id"], date=today.isoformat()):
            if m.get("kind") == "produce":
                made[m["item_id"]] = made.get(m["item_id"], 0) + abs(float(m.get("qty") or 0))
        return {**prep_list(plan["lines"], recipes, days_left, made), "date": today.isoformat(), "location_id": plan["location_id"]}
    run(ctx, body)
