# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for planning-service."""
from grepx_service import ActionDispatcher

from dto import PlanningAction
from . import production_target, reorder, set_target, warehouse_in, warehouse_out

TABLE = "planning_requests"
ROUTES = {
    PlanningAction.PRODUCTION_TARGET: production_target.handle,
    PlanningAction.SET_TARGET: set_target.handle,
    PlanningAction.WAREHOUSE_OUT: warehouse_out.handle,
    PlanningAction.WAREHOUSE_IN: warehouse_in.handle,
    PlanningAction.REORDER: reorder.handle,
}
handle = ActionDispatcher(ROUTES, PlanningAction, TABLE)
