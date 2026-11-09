# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""ADJUST - correct a counting error: set the right quantity, with a reason (R3, INV-08). Who may: ACC-03, checked at the edge."""
from grepx_service import RequestContext

from dto import MovementKind, ReasonCode
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(book):
        if len(ctx.text("note")) < 3:
            raise Stop(ReasonCode.REASON_REQUIRED)
        place, lines = book.location(), book.lines(allow_zero=True)
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.ADJUST.value, "set": l["qty"]}
                            for l in lines], items)
    run(ctx, body)
