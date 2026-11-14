# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RETURN - goods sent back to the supplier (short-dated, damaged, wrong). They leave stock at once; not a cost of goods -
the supplier credits them (payables-service RETURN_GOODS asks for this)."""
from grepx_service import RequestContext

from dto import MovementKind
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(book):
        place, lines = book.location(), book.lines()
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.RETURN.value, "delta": -l["qty"]}
                            for l in lines], items, {"supplier_id": ctx.text("supplier_id"), "return_reason": ctx.text("reason")[:120]})
    run(ctx, body)
