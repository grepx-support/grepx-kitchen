# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""WAREHOUSE_OUT - what to send a location from the holding place: enough for its days of cover (R4, INV-02..04)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import warehouse_out
from dto import ReasonCode
from .common import Stop, run, total


def handle(ctx: RequestContext) -> None:
    def body(view):
        target = view.location("to_location_id")
        if target.get("holding"):
            raise Stop(ReasonCode.UNKNOWN_LOCATION)
        holding = [l["_key"] for l in view.locations() if l.get("holding")]
        stock = view.stock()
        items = view.items() if target.get("kind") == gc.business.LocationKind.KITCHEN.value else \
            view.items(gc.item.ItemKind.FINISHED.value, gc.item.ItemKind.INGREDIENT.value, gc.item.ItemKind.SUPPLY.value)
        result = warehouse_out(items, view.usage(), target["_key"], stock.get(target["_key"], {}), total(stock, set(holding)),
                               int(target.get("days_of_cover") or 3))
        return {**result, "to_location_id": target["_key"], "from_location_id": holding[0] if holding else ""}
    run(ctx, body)
