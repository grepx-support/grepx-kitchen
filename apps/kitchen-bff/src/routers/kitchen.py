# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Kitchen: this week's target on the phone, record production runs and ingredients used (KIT-03..10)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/kitchen", tags=["kitchen"])
KIT = "kitchen"


@router.get("/target")
def target(location_id: str, k: Kitchen = Depends(allow("kitchen", "manage_business", module=KIT))):
    return k.cmd(gc.planning.REQUESTS, gc.planning.SERVICE, {"action": "PRODUCTION_TARGET", "location_id": location_id})["plan"]


@router.post("/target")
def set_target(body: dict, k: Kitchen = Depends(allow("manage_business", module=KIT))):
    """KIT-10 / Q12: type this week's target by hand, or add an event week's extra; empty = back to the calculation."""
    return k.cmd(gc.planning.REQUESTS, gc.planning.SERVICE, {"action": "SET_TARGET", "item_id": body.get("item_id"),
                                                             "qty": body.get("qty"), "extra": body.get("extra")})["plan"]


@router.post("/production")
def production(body: dict, k: Kitchen = Depends(allow("kitchen", module=KIT))):
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "PRODUCE", "location_id": body.get("location_id"),
                                                       "lines": body.get("lines") or []})


@router.post("/use")
def use(body: dict, k: Kitchen = Depends(allow("kitchen", module=KIT))):
    return k.cmd(gc.stock.REQUESTS, gc.stock.SERVICE, {"action": "USE", "location_id": body.get("location_id"),
                                                       "lines": body.get("lines") or []})


@router.get("/today")
def today(location_id: str, k: Kitchen = Depends(allow("kitchen", "manage_business", module=KIT))):
    """What this kitchen recorded today (production runs and ingredient use)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    day = datetime.now(ZoneInfo(k.business.get("timezone") or "UTC")).date().isoformat()
    items = k.items()
    rows = [r for r in k.rows(gc.stock.STOCK_MOVEMENTS, location_id=location_id, date=day) if r.get("kind") in ("produce", "use")]
    return {"date": day, "records": [{"kind": r["kind"], "item_name": items.get(r["item_id"], {}).get("name", ""), "qty": abs(r["qty"]),
                                      "unit": items.get(r["item_id"], {}).get("unit", ""), "by": r.get("user_name", ""), "at": r.get("at", "")}
                                     for r in sorted(rows, key=lambda r: r.get("at", ""), reverse=True)]}
