# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What an item costs a customer: their own fixed price for it, else the item's quantity price break for that many
(cheaper per unit when they take more), else its list price - less the customer's standing discount (not on a fixed
price). Charges (freight, delivery, service) are lines kept apart from goods, so reports can show them on their own."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from grepx_money import priced as money_priced

from dto import ReasonCode

CHARGES = ("freight", "delivery", "service", "other")


def amount(value, reason=ReasonCode.INVALID_PRICE) -> Decimal:
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(reason)
    if v < 0 or v > 10 ** 9:
        raise ValueError(reason)
    return v


def plain(d: Decimal) -> str:
    """10, 7.5 - never 1E+1."""
    return format(d.normalize(), "f")


def clean_pricing(raw) -> dict:
    """A customer's terms: discount % on everything, and fixed prices per item ({item_id: price})."""
    raw = raw or {}
    pct = amount(raw.get("discount_pct") or 0, ReasonCode.INVALID_DISCOUNT)
    if pct > 100:
        raise ValueError(ReasonCode.INVALID_DISCOUNT)
    prices = {str(k): plain(amount(v)) for k, v in (raw.get("prices") or {}).items() if str(v).strip() not in ("", "None")}
    return {"discount_pct": plain(pct), "prices": prices}


def clean_breaks(raw) -> list[dict]:
    """[{min_qty, price}]: more than one unit each, no two for the same quantity; smallest first."""
    out = {}
    for b in raw or []:
        q = amount(b.get("min_qty"), ReasonCode.INVALID_QUANTITY)
        if q <= 1:
            raise ValueError(ReasonCode.INVALID_QUANTITY)
        out[q] = amount(b.get("price"))
    return [{"min_qty": plain(q), "price": plain(p)} for q, p in sorted(out.items())]


def price_for(item: dict, qty, pricing: dict | None, breaks: list[dict] | None) -> dict:
    """{unit_price, discount, source}: source is customer / break / list."""
    pricing, qty = pricing or {}, Decimal(str(qty or 1))
    fixed = (pricing.get("prices") or {}).get(item.get("_key") or item.get("item_id") or "")
    if fixed is not None:
        return {"unit_price": str(fixed), "discount": "0", "source": "customer"}
    hit = [b for b in breaks or [] if Decimal(b["min_qty"]) <= qty]
    price, source = (hit[-1]["price"], "break") if hit else (str(item.get("price") or 0), "list")
    return {"unit_price": price, "discount": pricing.get("discount_pct") or "0", "source": source}


def fill_prices(lines: list[dict], items: dict[str, dict], pricing: dict | None, breaks_of: dict[str, list]) -> list[dict]:
    """Lines of an item without a price typed get the customer's price; charge lines are tagged and keep theirs."""
    out = []
    for raw in lines or []:
        line = dict(raw)
        if line.get("charge") and line["charge"] not in CHARGES:
            raise ValueError(ReasonCode.INVALID_CHARGE)
        item = items.get(line.get("item_id") or "")
        if item and str(line.get("unit_price") or "").strip() == "" and not line.get("charge"):
            got = price_for({**item, "_key": line["item_id"]}, line.get("qty"), pricing, breaks_of.get(line["item_id"]))
            line = {**line, "unit_price": got["unit_price"], "discount": line.get("discount") or got["discount"], "price_source": got["source"]}
        out.append(line)
    return out


def tag_charges(raw_lines: list[dict], clean: list[dict]) -> list[dict]:
    """Carry the charge tag and price source onto the checked lines (empty rows were dropped, in the same order)."""
    kept = [r for r in raw_lines or [] if str(r.get("description") or "").strip() or r.get("item_id") or r.get("qty")]
    return [{**c, **({"charge": r["charge"]} if r.get("charge") else {}), **({"price_source": r["price_source"]} if r.get("price_source") else {})}
            for c, r in zip(clean, kept)]


def charges_total(lines: list[dict]) -> int:
    return sum(int(l["amount"]) for l in lines if l.get("charge"))


def priced(doc: dict) -> dict:
    """Totals worked out from the lines (grepx_money), with the charges among them shown on their own."""
    return {**money_priced(doc), "charges": charges_total(doc["lines"])}
