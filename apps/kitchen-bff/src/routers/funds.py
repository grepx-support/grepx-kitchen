# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Funds (fund-service), for the owner: every fund and the business's totals, one fund in full, funds, parties and
movements. Amounts go out in minor units (cents / paise) with their currency; the web shows them as money."""
from datetime import date, timedelta

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/funds", tags=["funds"])
owner = allow("manage_business")


def ask(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.fund.REQUESTS, gc.fund.SERVICE, {"action": action, **fields})


@router.get("")
def overview(k: Kitchen = Depends(owner)):
    return {**ask(k, "OVERVIEW"), "currency": k.business.get("currency", "")}


def last_months(n: int = 3) -> list[str]:
    today = date.today().replace(day=1)
    out = []
    for _ in range(n):
        today = (today - timedelta(days=1)).replace(day=1)
        out.append(today.isoformat()[:7])
    return out


def actual_ebitda(k: Kitchen, fund_id: str) -> dict[str, list[float]]:
    """A use named like one of the business's places gets that place's EBITDA (sales less ingredients, labour, rent and
    other costs) for each of the last three months that had sales - the Costs page's own numbers."""
    plan = (k.one(gc.fund.FUNDS, fund_id) or {}).get("plan") or {}
    places = {r.get("name", ""): r["_key"] for r in k.rows(gc.business.LOCATIONS)}
    out: dict[str, list[float]] = {}
    for use in plan.get("uses") or []:
        loc = places.get(use.get("purpose", ""))
        if not loc:
            continue
        for m in last_months():
            s = k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SUMMARY", "month": m, "location_id": loc})["summary"]
            if s.get("sales") and s.get("net_profit") is not None:
                out.setdefault(use["purpose"], []).append(float(s["net_profit"]))
    return out


@router.get("/{fund_id}")
def one(fund_id: str, k: Kitchen = Depends(owner)):
    return {**ask(k, "FUND", fund_id=fund_id, actuals=actual_ebitda(k, fund_id)), "people": ask(k, "OVERVIEW")["parties"],
            "places": sorted(r.get("name", "") for r in k.rows(gc.business.LOCATIONS))}


@router.put("/{fund_id}/plan")
def plan(fund_id: str, body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "SET_PLAN", fund_id=fund_id, plan=body)["plan"]


@router.post("")
def save_fund(body: dict, k: Kitchen = Depends(owner)):
    fields = {f: body.get(f) for f in ("fund_id", "name", "kind", "currency", "target", "rate_pct", "purpose", "opened", "closed") if body.get(f) is not None}
    return ask(k, "SAVE_FUND", **{"currency": k.business.get("currency", ""), **fields})["fund"]


@router.post("/parties")
def save_party(body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "SAVE_PARTY", **{f: body.get(f) for f in ("party_id", "name", "kind", "email", "phone", "note")})["party"]


@router.post("/{fund_id}/entries")
def record(fund_id: str, body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "RECORD", fund_id=fund_id, **{f: body.get(f) for f in ("kind", "amount", "currency", "date", "due", "party_id", "purpose", "ref", "note")})["entry"]


@router.post("/entries/{entry_id}/reverse")
def reverse(entry_id: str, body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "REVERSE", entry_id=entry_id, reason=body.get("reason"))
