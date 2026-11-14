# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Supplier prices from their bills: every price paid per item (after the line discount), each new price against that
supplier's last one for the item, and which rises are jumps (at least the owner's percentage). Pure."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

LIVE = ("entered", "approved", "paid")


def unit_cost(line: dict) -> int:
    """Cents per unit after the line's own discount."""
    off = Decimal(str(line.get("discount") or 0))
    return int((Decimal(int(line["unit_price"])) * (100 - off) / 100).quantize(Decimal(1), ROUND_HALF_UP))


def points(bills: list[dict]) -> list[dict]:
    """Every item price on a bill that still counts, oldest first."""
    out = [{"supplier_id": b["supplier_id"], "supplier_name": b.get("supplier_name", ""), "item_id": l["item_id"], "description": l.get("description", ""),
            "unit": l.get("unit", ""), "date": b.get("bill_date", ""), "at": b.get("entered_at", ""), "price": unit_cost(l), "bill_id": b["bill_id"],
            "supplier_ref": b.get("supplier_ref", "")}
           for b in bills if b.get("state") in LIVE for l in b.get("lines") or [] if l.get("item_id")]
    return sorted(out, key=lambda p: (p["date"], p["at"]))


def last_price(history: list[dict], supplier_id: str, item_id: str, on: str, bill_id: str) -> dict | None:
    """The supplier's latest earlier price for the item (bills dated up to that day, this bill left out)."""
    before = [p for p in history if p["supplier_id"] == supplier_id and p["item_id"] == item_id and p["bill_id"] != bill_id and p["date"] <= on]
    return before[-1] if before else None


def changes(lines: list[dict], supplier_id: str, on: str, bill_id: str, history: list[dict], jump_pct) -> list[dict]:
    """Each billed item whose price differs from the supplier's last one: from, to, % change, jump or not."""
    out = []
    for line in lines:
        if not line.get("item_id"):
            continue
        was, now = last_price(history, supplier_id, line["item_id"], on, bill_id), unit_cost(line)
        if was is None or not was["price"] or was["price"] == now:
            continue
        pct = round((now - was["price"]) * 100 / was["price"], 1)
        out.append({"item_id": line["item_id"], "description": line.get("description", ""), "unit": line.get("unit", ""), "from": was["price"], "to": now,
                    "pct": pct, "since": was["date"], "jump": pct >= float(jump_pct or 10)})
    return out
