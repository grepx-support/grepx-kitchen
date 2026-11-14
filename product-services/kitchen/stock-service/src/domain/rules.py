# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""How a request changes stock.

Every change is a list of (location, item, delta) or (location, item, set-to) steps; apply() turns the current
quantities into the new ones and the movement rows that explain them. Quantities may go below zero: the system follows
what people record and the next count corrects it (Q6) - blocking a delivery because the books are behind would stop work.
"""
from __future__ import annotations


def level_key(location_id: str, item_id: str) -> str:
    return f"{location_id}:{item_id}"


def _number(value) -> float:
    try:
        number = round(float(value), 4)
    except (TypeError, ValueError):
        raise ValueError("INVALID_QUANTITY")
    if number < 0 or number > 1_000_000:
        raise ValueError("INVALID_QUANTITY")
    return int(number) if number.is_integer() else number


def clean_lines(lines, allow_zero: bool = False) -> list[dict]:
    """[{item_id, qty}] with each item once (quantities of repeated items add up)."""
    merged: dict[str, float] = {}
    for line in lines or []:
        item = str((line or {}).get("item_id") or "").strip()
        if not item:
            raise ValueError("UNKNOWN_ITEM")
        qty = _number(line.get("qty"))
        if qty == 0 and not allow_zero:
            continue
        merged[item] = round(merged.get(item, 0) + qty, 4)
    if not merged:
        raise ValueError("NO_LINES")
    return [{"item_id": k, "qty": int(v) if float(v).is_integer() else v} for k, v in merged.items()]


def apply(levels: dict[str, float], steps: list[dict]) -> tuple[dict[str, float], list[dict]]:
    """steps: {location_id, item_id, kind, delta} or {..., set: qty}. Returns (new levels by key, movements)."""
    after, moves = dict(levels), []
    for step in steps:
        key = level_key(step["location_id"], step["item_id"])
        before = after.get(key, 0)
        new = step["set"] if "set" in step else round(before + step["delta"], 4)
        new = int(new) if float(new).is_integer() else new
        change = round(new - before, 4)
        after[key] = new
        moves.append({**{k: v for k, v in step.items() if k not in ("delta", "set")},
                      "qty": int(change) if float(change).is_integer() else change, "before": before, "after": new})
    return after, moves
