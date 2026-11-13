# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Profit per product and per customer for a period: every line of the issued invoices in it (after the invoice's own
discount, before tax) against what those goods cost, credit notes taken off. Cost = quantity x the item's cost today
(for a product the kitchen makes, with no cost of its own: what its recipe's ingredients cost per unit made), so it is
an estimate when prices moved. Lines that are not an item (delivery, a service) have no cost. Pure; cents."""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from grepx_money import cents, percent_of

from dto import InvoiceState as S, Kind, ReasonCode

OTHER = "other"           # the group for lines that are not an item


def period(start: str, end: str, today: str) -> tuple[str, str]:
    """The period asked for; by default the month so far. Refuses INVALID_DATE (bad date, or start after end)."""
    start, end = start or today[:8] + "01", end or today
    try:
        a, b = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError):
        raise ValueError(ReasonCode.INVALID_DATE)
    if a > b:
        raise ValueError(ReasonCode.INVALID_DATE)
    return start, end


def margin(revenue: int, profit: int) -> float | None:
    return round(profit * 100 / revenue, 1) if revenue else None


def _cost(qty: Decimal, unit_cost: Decimal) -> int:
    return int((qty * unit_cost).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def unit_costs(items: dict[str, dict], recipes: dict[str, dict]) -> dict[str, tuple[Decimal, str]]:
    """Cents per unit for each item and where it came from: "item" (its own cost), "recipe" (ingredients / batch
    output) or "" (none known)."""
    own = {k: Decimal(cents(v.get("cost") or 0)) for k, v in items.items()}
    out = {}
    for key in items:
        recipe = recipes.get(key) or {}
        batch = Decimal(str(recipe.get("batch_output") or 0))
        if own[key] > 0:
            out[key] = (own[key], "item")
        elif batch > 0 and recipe.get("ingredients"):
            out[key] = (sum((Decimal(str(i["qty"])) * own.get(i["item_id"], Decimal(0)) for i in recipe["ingredients"]), Decimal(0)) / batch, "recipe")
        else:
            out[key] = (Decimal(0), "")
    return out


def _blank(**extra) -> dict:
    return {"revenue": 0, "cost": 0, "qty": Decimal(0), "invoices": set(), "customers": set(), **extra}


def _finish(row: dict) -> dict:
    out = {**row, "profit": row["revenue"] - row["cost"], "qty": str(row["qty"].normalize()),
           "invoices": len(row["invoices"]), "customers": len(row["customers"])}
    out["margin"] = margin(out["revenue"], out["profit"])
    return out


def margins(invoices: list[dict], items: dict[str, dict], names: dict[str, str], start: str, end: str, recipes: dict | None = None) -> dict:
    costs = unit_costs(items, recipes or {})
    by_item, by_customer = {}, {}
    for inv in invoices:
        if inv.get("state") not in (S.ISSUED.value, S.PAID.value) or not start <= (inv.get("issued") or "") <= end:
            continue
        sign = -1 if inv.get("kind") == Kind.CREDIT.value else 1
        cust = inv.get("customer_id", "")
        for line in inv.get("lines") or []:
            item = items.get(line.get("item_id") or "")
            key = line["item_id"] if item else OTHER
            row = by_item.setdefault(key, _blank(item_id=key if item else "", name=(item or {}).get("name") or "Other lines (not an item)",
                                                 unit=(item or {}).get("unit", ""), cost_from=costs[key][1] if item else ""))
            amount = line["amount"] - percent_of(line["amount"], inv.get("discount_rate") or 0)
            qty = Decimal(str(line["qty"]))
            cost = _cost(qty, costs[key][0]) if item else 0
            row["revenue"] += sign * amount
            row["cost"] += sign * cost
            row["qty"] += sign * qty if item else 0
            row["invoices"].add(inv.get("invoice_id"))
            row["customers"].add(cust)
            c = by_customer.setdefault(cust, _blank(customer_id=cust, name=names.get(cust) or inv.get("customer_name") or "Customer"))
            c["revenue"] += sign * amount
            c["cost"] += sign * cost
            c["invoices"].add(inv.get("invoice_id"))
    products = sorted((_finish(r) for r in by_item.values()), key=lambda r: -r["profit"])
    customers = sorted(({k: v for k, v in _finish(r).items() if k not in ("qty", "customers")} for r in by_customer.values()), key=lambda r: -r["profit"])
    revenue, cost = sum(r["revenue"] for r in products), sum(r["cost"] for r in products)
    return {"from": start, "to": end, "products": products, "customers": customers,
            "total": {"revenue": revenue, "cost": cost, "profit": revenue - cost, "margin": margin(revenue, revenue - cost)},
            "below_cost": [r["name"] for r in products if r["item_id"] and r["profit"] < 0],
            "no_cost": [r["name"] for r in products if r["item_id"] and not r["cost_from"]]}
