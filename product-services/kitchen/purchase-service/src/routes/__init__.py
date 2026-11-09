# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for purchase-service."""
from grepx_service import ActionDispatcher

from dto import PurchaseAction
from . import cancel, copy, receive, save

TABLE = "purchase_requests"
ROUTES = {
    PurchaseAction.SAVE: save.handle,
    PurchaseAction.COPY: copy.handle,
    PurchaseAction.CANCEL: cancel.handle,
    PurchaseAction.RECEIVE: receive.handle,
}
handle = ActionDispatcher(ROUTES, PurchaseAction, TABLE)
