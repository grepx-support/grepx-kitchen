# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""APPROVE - the owner says yes (approve = true) or no (with a note) to an order above their approval amount."""
from grepx_service import RequestContext, now_iso

from domain import decide
from dto import Table
from .common import business, order, run


def handle(ctx: RequestContext) -> None:
    def body():
        biz = business(ctx)
        po = {k: v for k, v in order(ctx, biz["_key"]).items() if not k.startswith("_")}
        po["approval"] = decide(po.get("approval"), bool(ctx.get("approve")), ctx.text("actor_name"), ctx.text("note"), now_iso())
        ctx.emitter.submit(Table.PURCHASE_ORDERS.value, po["po_id"], "ACCEPTED", po)
        return po
    run(ctx, body)
