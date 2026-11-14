# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""BREAK_DOWN - break bulk stock into its parts at a location (a whole chicken into breasts, thighs, wings; a sack into
bags): the item leaves, its parts arrive - the item's own recipe for it (breaks_into) or what really came out. Not a cost
of goods: value moves from the item to its parts."""
from grepx_service import RequestContext

from domain.parts import break_down
from dto import MovementKind, ReasonCode
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(book):
        place, lines = book.location(), book.lines()
        if len(lines) != 1:
            raise Stop(ReasonCode.ONE_ITEM_ONLY)
        source = lines[0]
        item = book.items(lines)[source["item_id"]]
        try:
            parts = break_down(item, source["qty"], ctx.get("outputs"))
        except ValueError as exc:
            raise Stop(str(exc))
        items = {**book.items(parts), source["item_id"]: item}
        steps = [{"location_id": place["_key"], "item_id": source["item_id"], "kind": MovementKind.BREAK_DOWN.value, "delta": -source["qty"]},
                 *[{"location_id": place["_key"], "item_id": p["item_id"], "kind": MovementKind.BREAK_DOWN.value, "delta": p["qty"]} for p in parts]]
        return book.record(steps, items, {"broken_down": source["item_id"]})
    run(ctx, body)
