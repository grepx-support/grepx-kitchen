# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for closing-service."""
from grepx_service import ActionDispatcher

from dto import ClosingAction
from . import submit

TABLE = "closing_requests"
ROUTES = {ClosingAction.SUBMIT: submit.handle}
handle = ActionDispatcher(ROUTES, ClosingAction, TABLE)
