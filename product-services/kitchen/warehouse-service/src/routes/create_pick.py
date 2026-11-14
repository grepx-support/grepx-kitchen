# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CREATE_PICK - a pick list for a warehouse-out: for each line, which lots to take from which bin, first expiry first."""
from grepx_service import RequestContext, new_key, now_iso

from domain import allocate, clean_lines
from dto import PickState, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(floor):
        source, target = floor.location("from_location_id"), floor.location("to_location_id")
        if source["_key"] == target["_key"]:
            raise Stop(ReasonCode.SAME_LOCATION)
        lines = clean_lines(ctx.get("lines"))
        items = floor.items(lines)
        out = []
        for line in lines:
            lots, short = allocate(floor.open_lots(source["_key"], line["item_id"]), line["qty"])
            out.append({**line, "name": items[line["item_id"]].get("name", ""), "unit": items[line["item_id"]].get("unit", ""),
                        "lots": lots, "short": short, "picked": 0})
        pick_id = new_key()[:12]
        row = {"pick_id": pick_id, "tenant_id": floor.tenant, "from_location_id": source["_key"], "to_location_id": target["_key"],
               "state": PickState.OPEN.value, "lines": out, "created_at": now_iso(), **floor.who()}
        return {"pick": floor.save(Table.PICKS.value, pick_id, row)}
    run(ctx, body)
