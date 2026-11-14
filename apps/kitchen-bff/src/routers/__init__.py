# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
from . import approvals, audit, bills, branding, chef, data, dispatch, funds, leave, payroll, pdf, roster, safety, team, closing, costs, inventory, kitchen, me, orders, forecast, outbox, platform, public, quotes, report, runs, sales, setup, stock, warehouse

ROUTERS = [me.router, approvals.router, audit.router, data.router, branding.router, dispatch.router, chef.router, funds.router, leave.router, payroll.router, pdf.router, roster.router, safety.router, team.router, platform.router, setup.router, stock.router, kitchen.router, orders.router, closing.router, costs.router,
           warehouse.router, runs.router, inventory.router, outbox.router, public.router, quotes.router, sales.router, bills.router, report.router, forecast.router]
