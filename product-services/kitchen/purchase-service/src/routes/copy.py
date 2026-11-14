# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COPY - start a new saved order from an earlier one (same supplier, place and lines)."""
from grepx_service import RequestContext

from .common import business, new_order, order, run


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        source = order(ctx, biz["_key"], open_only=False)
        lines = [{"item_id": l["item_id"], "qty": l["qty"]} for l in source.get("lines") or []]
        return new_order(ctx, biz, source["supplier_id"], source["location_id"], lines, source.get("note", ""))
    run(ctx, body)
