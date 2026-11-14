# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Items made of other items, and items that break into others:
  components  - a combo / meal box / kit: selling one takes its parts out of stock (one box = 1 rice + 1 curry + 1 drink);
  breaks_into - one unit of this gives these (a whole chicken = 2 breasts + 2 thighs + 2 wings + 1 carcass).
Pure."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

MAX_PARTS = 30


def clean_parts(raw, own_id: str = "") -> list[dict]:
    """[{item_id, qty}] -> checked (same item twice is added up). Refuses INVALID_PART (itself, bad or zero qty), TOO_MANY_PARTS."""
    out: dict[str, Decimal] = {}
    for r in raw or []:
        item = str((r or {}).get("item_id") or "")
        if not item:
            continue
        try:
            qty = Decimal(str(r.get("qty")))
        except (InvalidOperation, TypeError):
            raise ValueError("INVALID_PART")
        if item == own_id or qty <= 0:
            raise ValueError("INVALID_PART")
        out[item] = out.get(item, Decimal(0)) + qty
    if len(out) > MAX_PARTS:
        raise ValueError("TOO_MANY_PARTS")
    return [{"item_id": k, "qty": format(v.normalize(), "f")} for k, v in out.items()]


def parts_cost(parts: list[dict], items: dict[str, dict]) -> float:
    """What the parts cost together (their current costs)."""
    return round(sum(float(p["qty"]) * float((items.get(p["item_id"]) or {}).get("cost") or 0) for p in parts), 4)
