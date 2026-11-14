# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""WASTE - stock thrown away, with why (expired, spoiled, damaged, overproduced, other). It leaves stock at once and
counts as used in that location's cost of goods; the reason feeds the waste report."""
from grepx_service import RequestContext

from dto import MovementKind, ReasonCode, WasteReason
from .common import Stop, run

REASONS = {r.value for r in WasteReason}


def handle(ctx: RequestContext) -> None:
    def body(book):
        reason = ctx.text("reason")
        if reason not in REASONS:
            raise Stop(ReasonCode.INVALID_WASTE_REASON)
        place, lines = book.location(), book.lines()
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.WASTE.value, "delta": -l["qty"]}
                            for l in lines], items, {"waste_reason": reason})
    run(ctx, body)
