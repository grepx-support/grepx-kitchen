# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""COUNT - what staff counted at closing replaces system stock; each difference is kept with the staff name (Q6, INV-11, CLS-08).
A closing with no counts still sends COUNT (no lines) so costing knows the day is closed."""
from grepx_service import RequestContext

from dto import MovementKind
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(book):
        place, lines = book.location(), book.lines(allow_zero=True, allow_empty=True)   # sales only: nothing counted
        items = book.items(lines)
        return book.record([{"location_id": place["_key"], "item_id": l["item_id"], "kind": MovementKind.COUNT.value, "set": l["qty"]}
                            for l in lines], items)
    run(ctx, body)
