# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for stock-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import StockAction
from . import adjust, count, produce, receive, send, transfer, use

TABLE = "stock_requests"
ROUTES = {
    StockAction.RECEIVE: receive.handle,
    StockAction.SEND: send.handle,
    StockAction.TRANSFER: transfer.handle,
    StockAction.PRODUCE: produce.handle,
    StockAction.USE: use.handle,
    StockAction.ADJUST: adjust.handle,
    StockAction.COUNT: count.handle,
}
handle = ActionDispatcher(ROUTES, StockAction, TABLE)
