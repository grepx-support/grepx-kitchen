# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
import grepx_contracts as gc

from grepx_bff import business, people
from kitchen import ACCESS
from people_hooks import OutletCosts, labour_into_costs
from . import api_keys, approvals, attachments, audit, bills, branding, chef, data, dispatch, pdf, safety, closing, costs, inventory, kitchen, me, orders, forecast, outbox, platform, public, quotes, report, runs, sales, setup, stock, warehouse

ROUTERS = [me.router, api_keys.router, approvals.router, attachments.router, audit.router, data.router, branding.router, dispatch.router, chef.router, pdf.router, safety.router, platform.router, setup.router, stock.router, kitchen.router, orders.router, closing.router, costs.router,
           warehouse.router, runs.router, inventory.router, outbox.router, public.router, quotes.router, sales.router, bills.router, report.router, forecast.router]

# Setup -> Features: a router whose feature is off refuses every call (the web hides its pages too, /me "features").
M = gc.business.Module
FEATURE_OF = [(safety.router, M.FOOD_SAFETY), (warehouse.router, M.WAREHOUSE), (runs.router, M.DELIVERY), (quotes.router, M.QUOTES), (sales.router, M.SALES),
              (bills.router, M.PURCHASING), (chef.router, M.CHEF), (forecast.router, M.FORECAST), (data.router, M.IMPORT_EXPORT)]

ROUTERS = ACCESS.gate_all(ROUTERS, [(r, f.value) for r, f in FEATURE_OF])

# Team, roster, leave, payroll, my work and funds are shared (grepx_bff.people); the kitchen adds its costs to them.
SHARED = people.routers(after_finalise=labour_into_costs, fund_costs=OutletCosts())
ROUTERS = business.ACCESS.gate_all([r for r, _ in SHARED], [(r, f) for r, f in SHARED if f]) + ROUTERS
