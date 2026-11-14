# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_PAR - an item's minimum and maximum at a location (minimum 0 and no maximum = no par level)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import clean_par
from dto import ReasonCode, Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(stock):
        place = stock.mine(gc.business.LOCATIONS, ctx.text("location_id"), ReasonCode.UNKNOWN_LOCATION)
        item = stock.mine(gc.item.ITEMS, ctx.text("item_id"), ReasonCode.UNKNOWN_ITEM)
        key = f"{place['_key']}:{item['_key']}"
        row = {"tenant_id": stock.tenant, "location_id": place["_key"], "item_id": item["_key"],
               **clean_par({"min": ctx.get("min"), "max": ctx.get("max")})}
        ctx.emitter.submit(Table.PAR_LEVELS.value, key, "ACCEPTED", row)
        return {"par": row}
    run(ctx, body)
