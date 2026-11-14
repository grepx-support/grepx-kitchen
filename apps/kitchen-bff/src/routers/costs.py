# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Cost of goods sold by day and by month, for one location or the whole business - only for roles that may see costs
(COS-03..09)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.views import clean
from kitchen import Kitchen, allow

router = APIRouter(prefix="/costs", tags=["costs"])
COS = "costing"
viewer = allow("view_costs", module=COS)


@router.get("/days")
def days(month: str, location_id: str = "", k: Kitchen = Depends(viewer)):
    rows = [r for r in (k.rows(gc.costing.COST_DAYS, location_id=location_id) if location_id else k.rows(gc.costing.COST_DAYS))
            if r.get("date", "").startswith(month)]
    settings = k.business.get("settings") or {}
    return {"days": [clean(r) for r in sorted(rows, key=lambda r: (r["date"], r.get("location_name", "")))], "currency": k.business.get("currency", ""),
            "cogs_range": [settings.get("cogs_min"), settings.get("cogs_max")]}


@router.get("/month")
def month(month: str, location_id: str = "", k: Kitchen = Depends(viewer)):
    return k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SUMMARY", "month": month, "location_id": location_id})["summary"]
