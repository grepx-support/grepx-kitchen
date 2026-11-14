# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Purchase order lines, receipt and the text sent to the supplier (ORD-03, ORD-05..07)."""
from __future__ import annotations


def _qty(value, allow_zero: bool = False) -> float:
    try:
        number = round(float(value), 4)
    except (TypeError, ValueError):
        raise ValueError("INVALID_QUANTITY")
    if number < 0 or (number == 0 and not allow_zero) or number > 1_000_000:
        raise ValueError("INVALID_QUANTITY")
    return int(number) if number.is_integer() else number


def clean_lines(lines) -> list[dict]:
    """[{item_id, qty, recommended?}] - zero lines dropped, an item listed twice adds up."""
    out: dict[str, dict] = {}
    for line in lines or []:
        item = str((line or {}).get("item_id") or "").strip()
        if not item:
            raise ValueError("UNKNOWN_ITEM")
        qty = _qty(line.get("qty"), allow_zero=True)
        if qty == 0:
            continue
        row = out.setdefault(item, {"item_id": item, "qty": 0})
        row["qty"] = round(row["qty"] + qty, 4)
        if line.get("recommended") not in (None, ""):
            row["recommended"] = _qty(line["recommended"], allow_zero=True)
    if not out:
        raise ValueError("NO_LINES")
    return list(out.values())


def received_lines(ordered: list[dict], changed: list[dict] | None) -> list[dict]:
    """ORD-07: receive in full (no changes) or with changed quantities; an item not on the order may arrive too."""
    if not changed:
        return [{"item_id": l["item_id"], "qty": l["qty"]} for l in ordered]
    got = {}
    for line in changed:
        item = str(line.get("item_id") or "")
        if not item:
            raise ValueError("UNKNOWN_ITEM")
        got[item] = _qty(line.get("qty"), allow_zero=True)
    return [{"item_id": i, "qty": q} for i, q in got.items() if q > 0]


def message(business: str, supplier: str, number: str, deliver_to: str, lines: list[dict], names: dict, note: str = "") -> str:
    """ORD-06: the order as plain text to paste into WhatsApp."""
    rows = [f"- {names.get(l['item_id'], {}).get('name', l['item_id'])}: {l['qty']} {names.get(l['item_id'], {}).get('unit', '')}".rstrip()
            for l in lines]
    text = [f"Order {number} from {business}", f"To: {supplier}", f"Deliver to: {deliver_to}", "", *rows]
    if note:
        text += ["", note]
    return "\n".join(text)
