# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Landed cost: what else it took to get the goods in (duty, freight, customs, insurance, labour), spread over the
bill's item lines - by value, quantity or weight - so each item's unit cost is what it really cost. Pure; money in cents."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from grepx_money import cents

KINDS = ("duty", "freight", "customs", "insurance", "labour", "other")
SPREADS = ("value", "qty", "weight")


def clean_costs(raw) -> list[dict]:
    """[{kind, amount, spread?, on_bill?, note?}] -> checked rows; on_bill: this supplier charged it on this bill
    (it is added to what you pay); otherwise someone else billed it and it only goes into the cost."""
    out = []
    for r in raw or []:
        if not r or r.get("amount") in (None, ""):
            continue
        kind, spread = str(r.get("kind") or "other"), str(r.get("spread") or "value")
        if kind not in KINDS:
            raise ValueError("INVALID_LANDED_COST")
        if spread not in SPREADS:
            raise ValueError("INVALID_SPREAD")
        amount = cents(r["amount"])
        if amount <= 0:
            raise ValueError("INVALID_AMOUNT")
        out.append({"kind": kind, "amount": amount, "spread": spread, "on_bill": bool(r.get("on_bill", True)), "note": str(r.get("note") or "")[:120]})
    return out


def _num(v) -> Decimal:
    try:
        return Decimal(str(v or 0))
    except InvalidOperation:
        return Decimal(0)


def _basis(line: dict, spread: str, items: dict) -> Decimal:
    if spread == "qty":
        return _num(line.get("qty"))
    if spread == "weight":
        return _num(line.get("qty")) * (_num((items.get(line.get("item_id")) or {}).get("weight")) or Decimal(1))
    return Decimal(line.get("amount") or 0)


def share(total: int, weights: list[Decimal]) -> list[int]:
    """total cents split by weights; the rounding cents go to the biggest so the parts add up exactly."""
    whole = sum(weights)
    if not whole or not weights:
        return [0] * len(weights)
    parts = [int((Decimal(total) * w / whole).to_integral_value()) for w in weights]
    parts[max(range(len(weights)), key=lambda n: weights[n])] += total - sum(parts)
    return parts


def spread(lines: list[dict], costs: list[dict], items: dict | None = None) -> list[dict]:
    """Each line with landed (extra cents) and landed_unit (what one unit really cost, cents as a plain decimal string).
    Only item lines carry landed cost."""
    items = items or {}
    extra = [0] * len(lines)
    goods = [n for n, l in enumerate(lines) if l.get("item_id")]
    for c in costs:
        parts = share(c["amount"], [_basis(lines[n], c["spread"], items) for n in goods])
        for n, p in zip(goods, parts):
            extra[n] += p
    out = []
    for l, x in zip(lines, extra):
        qty = _num(l.get("qty"))
        unit = (Decimal(l.get("amount") or 0) + x) / qty if qty else Decimal(0)
        out.append({**l, "landed": x, "landed_unit": format(unit.quantize(Decimal("0.01")), "f")})
    return out


def landed(bill: dict, costs: list[dict], items: dict | None = None) -> dict:
    """The bill with its landed costs: lines spread, landed_total, and what is on this bill added to the total."""
    on_bill = sum(c["amount"] for c in costs if c["on_bill"])
    return {**bill, "lines": spread(bill["lines"], costs, items), "landed_costs": costs,
            "landed_total": sum(c["amount"] for c in costs), "landed_on_bill": on_bill, "total": bill["total"] + on_bill}


def new_costs(bill: dict) -> dict[str, str]:
    """item_id -> its landed unit cost in money (2 dp string), from an approved bill: the cost to use from now on."""
    out = {}
    for l in bill.get("lines") or []:
        if l.get("item_id") and l.get("landed_unit"):
            out[l["item_id"]] = format((Decimal(l["landed_unit"]) / 100).quantize(Decimal("0.0001")).normalize(), "f")
    return out
