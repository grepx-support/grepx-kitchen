# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Audit trail for the owner: who changed what and when, done or refused, over the last days."""
from datetime import datetime, timedelta, timezone

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow
from views.audit import AREAS, entries

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def audit(days: int = 7, k: Kitchen = Depends(allow("manage_business"))):
    days = max(1, min(days, 90))
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
    by_area = {area: k.rows(getattr(gc, area).REQUESTS, f"occurred_at >= '{since}'") for area in AREAS}
    names = {r["_key"]: r.get("name", "") for t in (gc.item.ITEMS, gc.business.LOCATIONS, gc.item.SUPPLIERS, gc.billing.CUSTOMERS)
             for r in k.rows(t)}
    rows = entries(by_area, names)
    return {"days": days, "entries": rows[:3000], "more": len(rows) > 3000}
