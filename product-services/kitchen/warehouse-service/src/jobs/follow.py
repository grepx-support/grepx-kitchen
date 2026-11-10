# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""stock_requests ACCEPTED -> lots follow the change (each request once: the followed table remembers it)."""
from __future__ import annotations

from datetime import date

import grepx_contracts as gc
from grepx_service import Emitter, Reader, now_iso

from domain import follow
from dto import Table


def follow_stock(app, row, cfg) -> str:
    f = row.fields
    changes = [c for c in f.get("changes") or [] if c.get("qty")]
    tenant = f.get("tenant_id", "")
    read = Reader(app.client)
    if not changes or not tenant or read.one(Table.FOLLOWED.value, row.key):
        return "skipped"
    places = {(c["location_id"], c["item_id"]) for c in changes}
    lots = {p: [l for l in read.accepted(Table.LOTS.value, tenant_id=tenant, location_id=p[0], item_id=p[1]) if l.get("qty", 0) > 0]
            for p in places}
    lots = {p: [{**l, "lot_id": l["_key"]} for l in ls] for p, ls in lots.items()}
    items = {i: (read.accepted_one(gc.item.ITEMS, i) or {}) for _, i in places}
    emitter = Emitter(app, cfg, cause=row)
    for lot in follow(row.key, f, changes, lots, items, str(f.get("date") or date.today().isoformat())):
        emitter.submit(Table.LOTS.value, lot["lot_id"], "ACCEPTED", {k: v for k, v in lot.items() if not k.startswith("_")})
    emitter.submit(Table.FOLLOWED.value, row.key, "ACCEPTED", {"tenant_id": tenant, "action": f.get("action"), "at": now_iso()})
    return "followed"
