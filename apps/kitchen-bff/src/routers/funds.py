# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Funds (fund-service), for the owner: every fund and the business's totals, one fund in full, funds, parties and
movements, investor statements. A use named like one of the business's places is linked to that place's real costs
(the Costs page: ingredients, labour, rent, other) so fund-service can show spent against given, burn, forecast and
suggestions. Amounts go out in minor units (cents / paise) with their currency; the web shows them as money."""
from datetime import date, timedelta

import grepx_contracts as gc
from fastapi import APIRouter, Depends

from documents import PdfFile, ReportPdf, brand, specs
from kitchen import Kitchen, allow

router = APIRouter(prefix="/funds", tags=["funds"])
owner = allow("manage_business")


def ask(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.fund.REQUESTS, gc.fund.SERVICE, {"action": action, **fields})


CATEGORIES = (("ingredient_cost", "Ingredients"), ("labour", "Labour"), ("rent", "Rent"), ("other", "Other costs"))


def months_back(n: int) -> list[str]:
    return list(reversed(last_months(n - 1))) + [date.today().isoformat()[:7]]


def summaries(k: Kitchen, location_ids: list[str], months: list[str]) -> dict[str, dict[str, dict]]:
    """{location_id: {month: costing summary}} in one request (not one per place and month)."""
    if not location_ids:
        return {}
    return k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SUMMARIES", "months": months, "location_ids": location_ids})["summaries"]


def spending(k: Kitchen, purposes: set[str], n: int = 6) -> dict[str, list[dict]]:
    """Each use that is one of the business's places: its costs per month and category (minor units), last n months."""
    places = {r.get("name", ""): r["_key"] for r in k.rows(gc.business.LOCATIONS)}
    used = sorted(purposes & set(places))
    grid = summaries(k, [places[p] for p in used], months_back(n))
    out: dict[str, list[dict]] = {}
    for purpose in used:
        for m, s in grid.get(places[purpose], {}).items():
            out.setdefault(purpose, []).extend({"month": m, "category": label, "amount": round(float(s.get(f) or 0) * 100)}
                                               for f, label in CATEGORIES if s.get(f))
    return out


def purposes(k: Kitchen, fund_id: str = "") -> set[str]:
    return {e.get("purpose") for e in k.rows(gc.fund.FUND_ENTRIES, **({"fund_id": fund_id} if fund_id else {})) if e.get("kind") == "allocate" and e.get("purpose")}


@router.get("")
def overview(as_of: str = "", k: Kitchen = Depends(owner)):
    base = k.business.get("currency", "")
    return {**ask(k, "OVERVIEW", base=base, as_of=as_of, spending=spending(k, purposes(k))), "currency": base,
            "places": sorted(r.get("name", "") for r in k.rows(gc.business.LOCATIONS))}


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
    uses = [(u["purpose"], places[u["purpose"]]) for u in plan.get("uses") or [] if places.get(u.get("purpose", ""))]
    grid = summaries(k, sorted({loc for _, loc in uses}), last_months())
    for purpose, loc in uses:
        for s in grid.get(loc, {}).values():
            if s.get("sales") and s.get("net_profit") is not None:
                out.setdefault(purpose, []).append(float(s["net_profit"]))
    return out


@router.get("/{fund_id}")
def one(fund_id: str, k: Kitchen = Depends(owner)):
    return {**ask(k, "FUND", fund_id=fund_id, actuals=actual_ebitda(k, fund_id), spending=spending(k, purposes(k, fund_id))),
            "people": [{"party_id": p["_key"], "name": p.get("name", "")} for p in k.rows(gc.fund.FUND_PARTIES)],
            "places": sorted(r.get("name", "") for r in k.rows(gc.business.LOCATIONS))}


@router.put("/{fund_id}/plan")
def plan(fund_id: str, body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "SET_PLAN", fund_id=fund_id, plan=body)["plan"]


@router.post("")
def save_fund(body: dict, k: Kitchen = Depends(owner)):
    fields = {f: body.get(f) for f in ("fund_id", "name", "kind", "currency", "target", "rate_pct", "rate_to_base", "purpose", "opened", "closed", "order")
              if body.get(f) not in (None, "")}
    return ask(k, "SAVE_FUND", **{"currency": k.business.get("currency", ""), **fields})["fund"]


@router.post("/parties")
def save_party(body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "SAVE_PARTY", **{f: body.get(f) for f in ("party_id", "name", "kind", "email", "phone", "note")})["party"]


@router.post("/{fund_id}/entries")
def record(fund_id: str, body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "RECORD", fund_id=fund_id, **{f: body.get(f) for f in ("kind", "amount", "currency", "rate", "date", "due", "party_id", "purpose", "ref", "note")})["entry"]


@router.post("/entries/{entry_id}/reverse")
def reverse(entry_id: str, body: dict, k: Kitchen = Depends(owner)):
    return ask(k, "REVERSE", entry_id=entry_id, reason=body.get("reason"))


@router.post("/order")
def reorder(body: dict, k: Kitchen = Depends(owner)):
    """Funds in the order they were dragged to."""
    for n, fund_id in enumerate(body.get("fund_ids") or []):
        ask(k, "SAVE_FUND", fund_id=fund_id, order=n + 1)
    return {"ok": True}


def statement_file(party_id: str, first: str, last: str, k: Kitchen) -> PdfFile:
    st = ask(k, "STATEMENT", party_id=party_id, first=first, last=last)["statement"]
    return PdfFile(ReportPdf(specs.investor_statement(st), brand(k)).build(), f"statement-{st['name'].replace(' ', '-')}-{st['last']}")


@router.get("/parties/{party_id}/statement")
def statement(party_id: str, first: str = "", last: str = "", k: Kitchen = Depends(owner)):
    return statement_file(party_id, first, last, k).response()


@router.post("/parties/{party_id}/statement/send")
def send_statement(party_id: str, body: dict, k: Kitchen = Depends(owner)):
    first, last = body.get("first", ""), body.get("last", "")
    file = statement_file(party_id, first, last, k)
    return ask(k, "SEND_STATEMENT", party_id=party_id, first=first, last=last, channels=body.get("channels") or ["email"],
               org=k.business.get("name", ""), attachments=[file.attachment(k.gw.storage)])["party"]
