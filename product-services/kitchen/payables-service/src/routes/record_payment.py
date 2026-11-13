# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECORD_PAYMENT - money paid to the supplier against an approved bill (part or all)."""
from grepx_service import RequestContext

from domain import pay
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        bill = pay(ap.bill(ctx.text("bill_id")), ctx.get("amount"), ctx.text("date") or ap.today(), ctx.text("method") or "bank",
                   ctx.text("reference"), ctx.text("actor_name"))
        return {"bill": ap.save(bill["bill_id"], bill)}
    run(ctx, body)
