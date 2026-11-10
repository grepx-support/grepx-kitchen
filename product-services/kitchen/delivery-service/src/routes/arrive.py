# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ARRIVE - the driver is at the stop."""
from grepx_service import RequestContext

from dto import StopState
from .common import run_action
from .stop_change import change


def handle(ctx: RequestContext) -> None:
    run_action(ctx, lambda fleet: fleet.save(change(fleet, StopState.ARRIVED.value, {})[0]))
