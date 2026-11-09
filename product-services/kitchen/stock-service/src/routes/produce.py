# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PRODUCE - a production run: staff, finished product, quantity made; adds finished goods (D6, KIT-06, KIT-08)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from dto import MovementKind, ReasonCode
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(book):
        kitchen = book.location()
        if kitchen.get("kind") != gc.business.LocationKind.KITCHEN.value:
            raise Stop(ReasonCode.NOT_A_KITCHEN)
        lines = book.lines()
        items = book.items(lines)
        if any(items[l["item_id"]].get("kind") != gc.item.ItemKind.FINISHED.value for l in lines):
            raise Stop(ReasonCode.NOT_FINISHED_GOOD)
        return book.record([{"location_id": kitchen["_key"], "item_id": l["item_id"], "kind": MovementKind.PRODUCE.value,
                             "delta": l["qty"]} for l in lines], items)
    run(ctx, body)
