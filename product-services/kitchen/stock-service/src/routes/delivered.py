# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""DELIVERED - the destination confirms a warehouse-out arrived (the delivery board: sent -> delivered).

Stock already moved when it was sent (SEND); this only records that it arrived, who confirmed it and when.
"""
from datetime import datetime, timezone

from grepx_service import RequestContext, state_of

from dto import DeliveryState, ReasonCode, Table
from .common import Book, Stop


def handle(ctx: RequestContext) -> None:
    try:
        book = Book(ctx)
    except Stop as stop:
        return ctx.reject(stop.args[0])
    key = ctx.text("delivery_id")
    row = ctx.read.accepted_one(Table.DELIVERIES.value, key) if key else None
    if row is None or row.get("tenant_id") != book.tenant:
        return ctx.reject(ReasonCode.UNKNOWN_DELIVERY)
    if row.get("state") == DeliveryState.DELIVERED.value:
        return ctx.reject(ReasonCode.ALREADY_DELIVERED)
    done = {**state_of(row), "state": DeliveryState.DELIVERED.value, "delivered_by": ctx.text("actor_name"),
            "delivered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": ctx.text("note")}
    ctx.emitter.submit(Table.DELIVERIES.value, key, "ACCEPTED", done)
    ctx.accept({"delivery": done})
