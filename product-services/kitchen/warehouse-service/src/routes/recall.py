# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECALL - a lot id or lot code: where every unit went (places, dishes, customers, waste), what is still on the shelf
to pull, and what it was made from. Read-only."""
from grepx_service import RequestContext

from domain.recall import start, trace
from dto import ReasonCode, Table


def handle(ctx: RequestContext) -> None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        return ctx.reject(ReasonCode.MISSING_TENANT)
    lots = [{**l, "lot_id": l["_key"]} for l in ctx.read.accepted(Table.LOTS.value, tenant_id=tenant)]
    lots = [{k: v for k, v in l.items() if not k.startswith("_")} for l in lots]
    first = start(lots, ctx.text("code"))
    if not first:
        return ctx.reject(ReasonCode.UNKNOWN_LOT)
    ctx.accept({"recall": {"code": ctx.text("code"), "start": first, **trace(first, lots)}})
