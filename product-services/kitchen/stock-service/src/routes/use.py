# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""USE - ingredients a kitchen used: staff, item, quantity; reduces ingredient stock (KIT-07, KIT-09)."""
from grepx_service import RequestContext

from dto import MovementKind
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(book):
        place, lines = book.location(), book.lines()
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.USE.value, "delta": -l["qty"]}
                            for l in lines], items)
    run(ctx, body)
