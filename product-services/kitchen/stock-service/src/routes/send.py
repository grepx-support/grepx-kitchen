# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND - warehouse out: stock leaves the holding place for a kitchen, store or truck (R1, INV-02/03/06)."""
from grepx_service import RequestContext

from dto import DeliveryState, MovementKind, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(book):
        source, target = book.location("from_location_id"), book.location("to_location_id")
        if source["_key"] == target["_key"]:
            raise Stop(ReasonCode.SAME_LOCATION)
        if not source.get("holding"):
            raise Stop(ReasonCode.NOT_HOLDING_LOCATION)
        lines = book.lines()
        items = book.items(lines)
        steps = []
        for l in lines:
            steps.append({"location_id": source["_key"], "item_id": l["item_id"], "kind": MovementKind.SEND_OUT.value,
                          "delta": -l["qty"], "other_location_id": target["_key"]})
            steps.append({"location_id": target["_key"], "item_id": l["item_id"], "kind": MovementKind.SEND_IN.value,
                          "delta": l["qty"], "other_location_id": source["_key"]})
        moves = book.record(steps, items)
        book.ctx.emitter.submit(Table.DELIVERIES.value, book.ctx.key, "ACCEPTED", {
            "delivery_id": book.ctx.key, "tenant_id": book.tenant, "state": DeliveryState.SENT.value,
            "from_location_id": source["_key"], "to_location_id": target["_key"], "date": moves[0]["date"],
            "sent_at": moves[0]["at"], "sent_by": book.ctx.text("actor_name"), "lines": len(lines)})
        return moves
    run(ctx, body)
