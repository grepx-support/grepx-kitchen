# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CHECK_ALERTS - look for low, negative, expiring and expired stock now; ACK_ALERT - an alert was dealt with."""
from grepx_service import RequestContext, now_iso, state_of

from alerting import check
from dto import ReasonCode, Table
from .common import run


def check_now(ctx: RequestContext) -> None:
    run(ctx, lambda stock: {"new": len(check(stock, ctx.emitter, ctx.text("link")))})


def ack(ctx: RequestContext) -> None:
    def body(stock):
        alert = stock.mine(Table.ALERTS.value, ctx.text("alert_id"), ReasonCode.UNKNOWN_ALERT)
        row = {**state_of(alert), "state": "done", "done_at": now_iso(), "done_by": ctx.text("actor_name")}
        ctx.emitter.submit(Table.ALERTS.value, alert["_key"], "ACCEPTED", row)
        return {"alert": row}
    run(ctx, body)
