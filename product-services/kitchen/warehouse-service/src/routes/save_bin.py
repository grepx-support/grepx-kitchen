# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_BIN - a shelf, bin, fridge or freezer in a location (code A-01, zone chilled ...)."""
from grepx_service import RequestContext, new_key

from domain import clean_bin
from dto import ReasonCode, Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        place = floor.location()
        bin_id = ctx.text("bin_id")
        if bin_id:
            floor.mine(Table.BINS.value, bin_id, ReasonCode.UNKNOWN_BIN)
        row = {"bin_id": bin_id or new_key()[:12], "tenant_id": floor.tenant, "location_id": place["_key"],
               **clean_bin({k: ctx.get(k) for k in ("code", "zone", "note", "active")})}
        return {"bin": floor.save(Table.BINS.value, row["bin_id"], row)}
    run(ctx, body)
