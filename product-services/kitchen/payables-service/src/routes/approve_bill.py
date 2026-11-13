# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""APPROVE_BILL - ok to pay. A bill that does not match its order needs a note."""
from grepx_service import RequestContext

from domain import approve
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        bill = approve(ap.bill(ctx.text("bill_id")), ctx.text("note"), ctx.text("actor_name"))
        return {"bill": ap.save(bill["bill_id"], bill)}
    run(ctx, body)
