# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""APPROVE_BILL - ok to pay. A bill that does not match its order needs a note. Unless told not to (recost false), each
item's cost becomes what it really cost on this bill, landed costs included (item-service SET_COSTS)."""
import grepx_contracts as gc
from grepx_service import RequestContext

from domain import approve
from domain.landed import new_costs
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        bill = approve(ap.bill(ctx.text("bill_id")), ctx.text("note"), ctx.text("actor_name"))
        costs = new_costs(bill) if bill.get("recost", True) else {}
        if costs:
            ctx.request(gc.item.REQUESTS, f"recost-{bill['bill_id']}",
                        {"action": gc.item.ItemAction.SET_COSTS.value, "tenant_id": ap.tenant, "costs": costs, "source": f"Bill {bill.get('supplier_ref', '')}",
                         "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.item.SERVICE)
        return {"bill": ap.save(bill["bill_id"], bill), "recosted": costs}
    run(ctx, body)
