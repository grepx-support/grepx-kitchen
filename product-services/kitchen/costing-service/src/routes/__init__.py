# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for costing-service."""
from grepx_service import ActionDispatcher

from dto import CostingAction
from . import copy_overheads, overheads, set_overhead, share_overhead, summary

TABLE = "costing_requests"
ROUTES = {
    CostingAction.SET_OVERHEAD: set_overhead.handle,
    CostingAction.SUMMARY: summary.handle,
    CostingAction.SHARE_OVERHEAD: share_overhead.handle,
    CostingAction.COPY_OVERHEADS: copy_overheads.handle,
    CostingAction.OVERHEADS: overheads.handle,
}
handle = ActionDispatcher(ROUTES, CostingAction, TABLE)
