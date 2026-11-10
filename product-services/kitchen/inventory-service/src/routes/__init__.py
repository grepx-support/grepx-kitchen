# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for inventory-service."""
from grepx_service import ActionDispatcher

from dto import InventoryAction
from . import alerts, reports, set_par, takes

TABLE = "inventory_requests"
ROUTES = {
    InventoryAction.SET_PAR: set_par.handle,
    InventoryAction.START_TAKE: takes.start,
    InventoryAction.COUNT_TAKE: takes.count,
    InventoryAction.FINISH_TAKE: takes.finish,
    InventoryAction.CANCEL_TAKE: takes.cancel,
    InventoryAction.CHECK_ALERTS: alerts.check_now,
    InventoryAction.ACK_ALERT: alerts.ack,
    InventoryAction.VALUATION: reports.value,
    InventoryAction.ANALYSIS: reports.analyse,
}
handle = ActionDispatcher(ROUTES, InventoryAction, TABLE)
