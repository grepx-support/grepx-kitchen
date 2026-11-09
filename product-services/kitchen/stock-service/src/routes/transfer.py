# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""TRANSFER - a store short of stock receives it from another store; one record moves it out and in (R2, INV-07)."""
from grepx_service import RequestContext

from dto import MovementKind, ReasonCode
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(book):
        source, target = book.location("from_location_id"), book.location("to_location_id")
        if source["_key"] == target["_key"]:
            raise Stop(ReasonCode.SAME_LOCATION)
        lines = book.lines()
        items = book.items(lines)
        steps = []
        for l in lines:
            steps.append({"location_id": source["_key"], "item_id": l["item_id"], "kind": MovementKind.TRANSFER_OUT.value,
                          "delta": -l["qty"], "other_location_id": target["_key"]})
            steps.append({"location_id": target["_key"], "item_id": l["item_id"], "kind": MovementKind.TRANSFER_IN.value,
                          "delta": l["qty"], "other_location_id": source["_key"]})
        return book.record(steps, items)
    run(ctx, body)
