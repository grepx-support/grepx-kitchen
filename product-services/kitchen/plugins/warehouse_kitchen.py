# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The kitchen's answers to the shared warehouse-service (plugins.warehouse): bins are shelves, fridges and freezers;
goods are the stock items (with their shelf life, so lots get an expiry); lots follow every stock change first expiry
first out; a finished pick list is a warehouse-out (stock-service SEND)."""
import grepx_contracts as gc

ZONES = ("dry", "chilled", "frozen", "packaging")
LOTS = True


def goods(read, tenant, ids):
    rows = {i: read.accepted_one(gc.item.ITEMS, i) for i in ids}
    return {i: r for i, r in rows.items() if r and r.get("tenant_id") == tenant}


def send(ctx, tenant, pick, lines):
    ctx.request(gc.stock.REQUESTS, f"pick-{pick['pick_id']}",
                {"action": gc.stock.StockAction.SEND.value, "tenant_id": tenant, "from_location_id": pick["from_location_id"],
                 "to_location_id": pick["to_location_id"], "lines": lines, "ref": pick["pick_id"], "note": "Pick list",
                 "actor_id": ctx.text("actor_id"), "actor_name": ctx.text("actor_name")}, gc.stock.SERVICE)
