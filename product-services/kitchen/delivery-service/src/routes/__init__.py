# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for delivery-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import DeliveryAction
from . import arrive, cancel_run, deliver, fail_stop, plan_run, set_stops, start_run

TABLE = "delivery_requests"
ROUTES = {
    DeliveryAction.PLAN_RUN: plan_run.handle,
    DeliveryAction.SET_STOPS: set_stops.handle,
    DeliveryAction.START_RUN: start_run.handle,
    DeliveryAction.ARRIVE: arrive.handle,
    DeliveryAction.DELIVER: deliver.handle,
    DeliveryAction.FAIL_STOP: fail_stop.handle,
    DeliveryAction.CANCEL_RUN: cancel_run.handle,
}
handle = ActionDispatcher(ROUTES, DeliveryAction, TABLE)
