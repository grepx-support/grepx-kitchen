# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Staff closing: the form (expected stock, sales types) and the submit (CLS-01..09)."""
from datetime import datetime
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.views import clean
from kitchen import Kitchen, allow, named

router = APIRouter(prefix="/closing", tags=["closing"])
CLS = "closing"


def today(k: Kitchen) -> str:
    try:
        return datetime.now(ZoneInfo(k.business.get("timezone") or "UTC")).date().isoformat()
    except Exception:
        return datetime.utcnow().date().isoformat()


@router.get("/form")
def form(location_id: str, k: Kitchen = Depends(allow("closing", module=CLS))):
    """CLS-03: the stock the system expects for each item at this location; staff only type what they count."""
    place = k.location(location_id)
    items = {i: r for i, r in k.items().items() if r.get("active", True)}
    levels = {r["item_id"]: r.get("qty", 0) for r in k.rows(gc.stock.STOCK_LEVELS, location_id=location_id)}
    lines = [{"item_id": i, "item_name": r.get("name", ""), "unit": r.get("unit", ""), "kind": r.get("kind", ""), "expected": levels.get(i, 0)}
             for i, r in items.items() if i in levels or r.get("kind") == gc.item.ItemKind.FINISHED.value]
    done = [c for c in k.rows(gc.closing.CLOSINGS, location_id=location_id)]
    last = max((c.get("date", "") for c in done), default="")
    return {"location": clean(place, ("name", "kind", "count_every_days")), "date": today(k), "submitted_today": last == today(k),
            "last_closing": last, "sales_types": (k.business.get("settings") or {}).get("sales_types") or ["Sales"], "staff_name": k.name,
            "lines": sorted(lines, key=lambda l: (l["kind"] != "finished", l["item_name"]))}


@router.post("")
def submit(body: dict, k: Kitchen = Depends(allow("closing", module=CLS))):
    return k.cmd(gc.closing.REQUESTS, gc.closing.SERVICE, {"action": "SUBMIT", "location_id": body.get("location_id"), "date": body.get("date", ""),
                                                           "staff_name": body.get("staff_name") or k.name, "issues": body.get("issues", ""),
                                                           "counts": body.get("counts") or [], "sales": body.get("sales") or {}})["closing"]


@router.get("/history")
def history(location_id: str = "", k: Kitchen = Depends(allow("manage_business", "view_costs", module=CLS))):
    """Q6: the owner reviews the differences between counts and system stock."""
    rows = k.rows(gc.closing.CLOSINGS, location_id=location_id) if location_id else k.rows(gc.closing.CLOSINGS)
    items = k.items()
    out = []
    for c in sorted(rows, key=lambda c: c.get("date", ""), reverse=True)[:60]:
        v = clean(c)
        v["counts"] = [{**l, "item_name": items.get(l["item_id"], {}).get("name", ""), "unit": items.get(l["item_id"], {}).get("unit", ""),
                        "difference": round(float(l["qty"]) - float(l.get("expected") or 0), 4)} for l in c.get("counts") or []]
        out.append(v)
    return {"closings": out}
