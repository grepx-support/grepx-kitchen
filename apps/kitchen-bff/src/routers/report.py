# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The owner's money reports: the monthly summary - sales (billing-service) and purchases (payables-service) for a year,
side by side, each service adding up its own documents and joined here month by month - and profit per product."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends, Query

from kitchen import Kitchen, allow

router = APIRouter(prefix="/money", tags=["money"])
owner = allow("manage_business")


def joined(sales: list[dict], buys: list[dict]) -> list[dict]:
    """One row per month: sales and purchases before tax, what is left (gross profit), tax charged less tax paid,
    and money in and out."""
    out = []
    for s, b in zip(sales, buys):
        out.append({"month": s["month"], "sales": s["sales"], "purchases": b["purchases"], "gross": s["sales"] - b["purchases"],
                    "tax_charged": s["tax"], "tax_paid": b["tax"], "tax_due": s["tax"] - b["tax"],
                    "received": s["received"], "paid": b["paid"], "invoices": s["invoices"], "credits": s["credits"], "bills": b["bills"]})
    return out


@router.get("/report")
def report(year: int | None = None, k: Kitchen = Depends(owner)):
    asked = {"year": year} if year else {}
    sales = k.cmd(gc.billing.REQUESTS, gc.billing.SERVICE, {"action": gc.billing.BillingAction.MONTHLY.value, **asked})
    buys = k.cmd(gc.payables.REQUESTS, gc.payables.SERVICE, {"action": gc.payables.PayablesAction.MONTHLY.value, **asked})
    months = joined(sales["months"], buys["months"])
    keys = [f for f in months[0] if f != "month"]
    return {"year": sales["year"], "months": months, "year_total": {f: sum(m[f] for m in months) for f in keys},
            "currency": k.business.get("currency", ""), "tax_label": (k.business.get("billing") or {}).get("tax_label") or "Tax"}


@router.get("/margins")
def margins(start: str = Query("", alias="from"), end: str = Query("", alias="to"), k: Kitchen = Depends(owner)):
    out = k.cmd(gc.billing.REQUESTS, gc.billing.SERVICE, {"action": gc.billing.BillingAction.MARGINS.value, "from": start, "to": end})
    return {**out, "currency": k.business.get("currency", "")}
