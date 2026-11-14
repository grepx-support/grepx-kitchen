# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""FAIL_STOP - could not deliver (closed, refused, no access...): the trip stays on the way and can go on another run."""
from grepx_service import RequestContext

from dto import ReasonCode, StopState
from .common import Stop, run_action
from .stop_change import change


def handle(ctx: RequestContext) -> None:
    def body(fleet):
        reason = " ".join(ctx.text("reason").split())[:200]
        if len(reason) < 3:
            raise Stop(ReasonCode.REASON_REQUIRED)
        return fleet.save(change(fleet, StopState.FAILED.value, {"fail_reason": reason})[0])
    run_action(ctx, body)
