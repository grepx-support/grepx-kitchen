# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import feature_on
from . import approvals, audit, bills, branding, chef, data, dispatch, funds, leave, payroll, pdf, roster, safety, team, closing, costs, inventory, kitchen, me, orders, forecast, outbox, platform, public, quotes, report, runs, sales, setup, stock, warehouse

ROUTERS = [me.router, approvals.router, audit.router, data.router, branding.router, dispatch.router, chef.router, funds.router, leave.router, payroll.router, pdf.router, roster.router, safety.router, team.router, platform.router, setup.router, stock.router, kitchen.router, orders.router, closing.router, costs.router,
           warehouse.router, runs.router, inventory.router, outbox.router, public.router, quotes.router, sales.router, bills.router, report.router, forecast.router]

# Setup -> Features: a router whose feature is off refuses every call (the web hides its pages too, /me "features").
M = gc.business.Module
FEATURE_OF = [(funds.router, M.FUNDS), (payroll.router, M.PAYROLL), (roster.router, M.ROSTER), (leave.router, M.LEAVE), (team.router, M.TEAM),
              (safety.router, M.FOOD_SAFETY), (warehouse.router, M.WAREHOUSE), (runs.router, M.DELIVERY), (quotes.router, M.QUOTES), (sales.router, M.SALES),
              (bills.router, M.PURCHASING), (chef.router, M.CHEF), (forecast.router, M.FORECAST), (data.router, M.IMPORT_EXPORT)]


def gated(router: APIRouter, feature: str) -> APIRouter:
    """The router's routes again, each first checking that its feature is on."""
    outer = APIRouter(dependencies=[Depends(feature_on(feature.value))])
    outer.include_router(router)
    return outer


_GATE = {id(r): f for r, f in FEATURE_OF}
ROUTERS = [gated(r, _GATE[id(r)]) if id(r) in _GATE else r for r in ROUTERS]
