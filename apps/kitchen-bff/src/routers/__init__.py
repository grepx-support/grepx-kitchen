# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
from . import closing, costs, inventory, kitchen, me, orders, outbox, platform, public, runs, setup, stock, warehouse

ROUTERS = [me.router, platform.router, setup.router, stock.router, kitchen.router, orders.router, closing.router, costs.router,
           warehouse.router, runs.router, inventory.router, outbox.router, public.router]
