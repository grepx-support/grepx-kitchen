# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECEIVE - stock arrives at a location (INV-06; a received purchase order sends this too - ORD-07)."""
from grepx_service import RequestContext

from dto import MovementKind
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(book):
        place, lines = book.location(), book.lines()
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.RECEIVE.value, "delta": l["qty"]}
                            for l in lines], items, {"supplier_id": ctx.text("supplier_id")})
    run(ctx, body)
