# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""VOID_BILL - entered by mistake (or a duplicate): cancelled, kept for the record. Not once something was paid."""
from grepx_service import RequestContext

from domain import void
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        bill = {**void(ap.bill(ctx.text("bill_id"))), "void_reason": ctx.text("reason")[:200], "voided_by": ctx.text("actor_name")}
        return {"bill": ap.save(bill["bill_id"], bill)}
    run(ctx, body)
