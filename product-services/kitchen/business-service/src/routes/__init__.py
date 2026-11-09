# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for business-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import BusinessAction
from . import create, save_location, update

TABLE = "business_requests"
ROUTES = {
    BusinessAction.CREATE: create.handle,
    BusinessAction.UPDATE: update.handle,
    BusinessAction.SAVE_LOCATION: save_location.handle,
}
handle = ActionDispatcher(ROUTES, BusinessAction, TABLE)
