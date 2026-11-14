# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Supplier returns: goods sent back against a bill. You can return up to what was billed (less what went back before);
the supplier credits each line at the billed price plus its tax, and the credit comes off what you owe - or, once paid,
is money they owe you back. Pure; money in cents."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from dto import BillState as S

REASONS = ("damaged", "short_dated", "wrong_item", "quality", "over_delivered", "other")


def returned(bill: dict) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for r in bill.get("returns") or []:
        for l in r["lines"]:
            out[l["item_id"]] = out.get(l["item_id"], Decimal(0)) + Decimal(l["qty"])
    return out


def returnable(bill: dict) -> dict[str, Decimal]:
    """item_id -> what can still go back: billed less returned."""
    back = returned(bill)
    out: dict[str, Decimal] = {}
    for l in bill.get("lines") or []:
        if l.get("item_id"):
            out[l["item_id"]] = out.get(l["item_id"], Decimal(0)) + Decimal(l["qty"])
    return {k: v - back.get(k, Decimal(0)) for k, v in out.items()}


def unit_price(bill: dict, item_id: str) -> int:
    line = next(l for l in bill["lines"] if l.get("item_id") == item_id)
    return int(line["unit_price"])


def return_goods(bill: dict, raw_lines: list, reason: str, note: str, day: str, by: str, key: str) -> dict:
    """The bill with one more return and its credit. Refuses: NOT_RETURNABLE (void bill), INVALID_REASON,
    NO_LINES, MORE_THAN_BILLED, INVALID_QUANTITY."""
    if bill.get("state") == S.VOID.value:
        raise ValueError("NOT_RETURNABLE")
    if reason not in REASONS:
        raise ValueError("INVALID_REASON")
    left, rate = returnable(bill), Decimal(str(bill.get("tax_rate") or 0))
    lines, sub = [], 0
    for raw in raw_lines or []:
        try:
            qty = Decimal(str(raw.get("qty") or 0))
        except InvalidOperation:
            raise ValueError("INVALID_QUANTITY")
        if qty == 0:
            continue
        item = str(raw.get("item_id") or "")
        if qty < 0:
            raise ValueError("INVALID_QUANTITY")
        if item not in left or qty > left[item]:
            raise ValueError("MORE_THAN_BILLED")
        amount = int((qty * unit_price(bill, item)).to_integral_value())
        desc = next(l["description"] for l in bill["lines"] if l.get("item_id") == item)
        lines.append({"item_id": item, "description": desc, "qty": format(qty.normalize(), "f"), "amount": amount})
        sub += amount
    if not lines:
        raise ValueError("NO_LINES")
    tax = int((Decimal(sub) * rate / 100).to_integral_value())
    entry = {"return_id": key, "date": day, "reason": reason, "note": note[:200], "by": by, "lines": lines, "subtotal": sub, "tax": tax, "credit": sub + tax}
    out = {**bill, "returns": [*(bill.get("returns") or []), entry], "credited": bill.get("credited", 0) + entry["credit"]}
    owed = out["total"] - out.get("paid", 0) - out["credited"]
    if owed <= 0 and out["state"] == S.APPROVED.value:
        out["state"] = S.PAID.value
    out["refund_due"] = max(0, -owed)
    return out
