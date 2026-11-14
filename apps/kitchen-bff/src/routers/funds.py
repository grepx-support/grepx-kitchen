# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Funds (fund-service), for the owner: every fund and the business's totals, one fund in full, funds, parties and
movements. Amounts go out in minor units (cents / paise) with their currency; the web shows them as money."""
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


@router.get("/{fund_id}")
def one(fund_id: str, k: Kitchen = Depends(owner)):
    return {**ask(k, "FUND", fund_id=fund_id), "people": ask(k, "OVERVIEW")["parties"]}


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
