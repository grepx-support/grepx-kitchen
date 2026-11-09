# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
from . import closing, costs, kitchen, me, orders, platform, setup, stock

ROUTERS = [me.router, platform.router, setup.router, stock.router, kitchen.router, orders.router, closing.router, costs.router]
