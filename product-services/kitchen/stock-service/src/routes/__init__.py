# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for stock-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import StockAction
from . import adjust, break_down, count, delivered, produce, receive, return_goods, sell, send, transfer, use, waste

TABLE = "stock_requests"
ROUTES = {
    StockAction.RECEIVE: receive.handle,
    StockAction.RETURN: return_goods.handle,
    StockAction.BREAK_DOWN: break_down.handle,
    StockAction.SEND: send.handle,
    StockAction.TRANSFER: transfer.handle,
    StockAction.PRODUCE: produce.handle,
    StockAction.USE: use.handle,
    StockAction.ADJUST: adjust.handle,
    StockAction.COUNT: count.handle,
    StockAction.DELIVERED: delivered.handle,
    StockAction.WASTE: waste.handle,
    StockAction.SELL: sell.handle,
}
handle = ActionDispatcher(ROUTES, StockAction, TABLE)
