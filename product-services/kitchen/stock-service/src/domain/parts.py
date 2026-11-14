# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Combos and breaking down, on the stock side. Pure."""
from __future__ import annotations


def expand(lines: list[dict], items: dict[str, dict]) -> list[dict]:
    """Lines with every combo replaced by its parts x quantity (same part from several combos added up); others as they are."""
    out: dict[str, float] = {}
    for l in lines:
        parts = (items.get(l["item_id"]) or {}).get("components") or []
        for item_id, qty in ([(p["item_id"], float(p["qty"]) * l["qty"]) for p in parts] if parts else [(l["item_id"], l["qty"])]):
            out[item_id] = round(out.get(item_id, 0) + qty, 4)
    return [{"item_id": k, "qty": v} for k, v in out.items()]


def break_down(item: dict, qty: float, outputs: list[dict] | None = None) -> list[dict]:
    """What qty units of item give: the outputs typed in (what really came out), else the item's breaks_into x qty.
    Refuses NOTHING_TO_BREAK_INTO."""
    got = [{"item_id": o["item_id"], "qty": float(o["qty"])} for o in outputs or [] if float(o.get("qty") or 0) > 0] if outputs else \
        [{"item_id": p["item_id"], "qty": round(float(p["qty"]) * qty, 4)} for p in item.get("breaks_into") or []]
    if not got:
        raise ValueError("NOTHING_TO_BREAK_INTO")
    return got
