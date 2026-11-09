# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""WAREHOUSE_IN - what the holding place needs for the coming week, all locations' demand included (INV-05)."""
from grepx_service import RequestContext

from domain import warehouse_in
from dto import ReasonCode
from .common import Stop, run, total


def handle(ctx: RequestContext) -> None:
    def body(view):
        place = view.location()
        if not place.get("holding"):
            raise Stop(ReasonCode.NOT_HOLDING_LOCATION)
        stock = view.stock()
        holding = {l["_key"] for l in view.locations() if l.get("holding")}
        others = {l["_key"] for l in view.locations()} - holding
        result = warehouse_in(view.items(), view.usage(), total(stock, holding), total(stock, others), view.safety())
        return {**result, "location_id": place["_key"]}
    run(ctx, body)
