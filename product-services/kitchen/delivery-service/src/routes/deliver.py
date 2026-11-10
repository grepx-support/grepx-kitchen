# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DELIVER - proof of delivery: who received it (and their signature); the trip is marked delivered in stock."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import check_signature
from dto import ReasonCode, StopState
from .common import Stop, run_action
from .stop_change import change


def handle(ctx: RequestContext) -> None:
    def body(fleet):
        receiver = " ".join(ctx.text("receiver").split())[:80]
        if len(receiver) < 2:
            raise Stop(ReasonCode.RECEIVER_REQUIRED)
        run, stop = change(fleet, StopState.DELIVERED.value, {"receiver": receiver, "signature": check_signature(ctx.get("signature")),
                                                            "note": ctx.text("note")[:300], "driver": ctx.text("actor_name")})
        ctx.request(gc.stock.REQUESTS, f"pod-{stop['delivery_id']}",
                    {"action": gc.stock.StockAction.DELIVERED.value, "tenant_id": fleet.tenant, "delivery_id": stop["delivery_id"],
                     "note": f"Received by {receiver}", "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")},
                    gc.stock.SERVICE)
        return fleet.save(run)
    run_action(ctx, body)
