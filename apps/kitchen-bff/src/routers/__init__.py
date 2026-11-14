# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
from . import audit, bills, chef, closing, costs, inventory, kitchen, me, orders, forecast, outbox, platform, public, report, runs, sales, setup, stock, warehouse

ROUTERS = [me.router, audit.router, chef.router, platform.router, setup.router, stock.router, kitchen.router, orders.router, closing.router, costs.router,
           warehouse.router, runs.router, inventory.router, outbox.router, public.router, sales.router, bills.router, report.router, forecast.router]
