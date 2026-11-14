# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""An item's cost moving: the new cost with where it came from, and the last few kept as history. Pure."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

HISTORY = 12


def recost(item: dict, cost, source: str, at: str) -> dict:
    """The item with its new cost; the old one goes into cost_history (newest first). Same cost: unchanged."""
    try:
        new = Decimal(str(cost))
    except InvalidOperation:
        raise ValueError("INVALID_COST")
    if new < 0:
        raise ValueError("INVALID_COST")
    old = Decimal(str(item.get("cost") or 0))
    if new == old:
        return item
    value = float(new)
    entry = {"cost": value, "was": float(old), "source": source[:80], "at": at}
    return {**item, "cost": value, "cost_changed_at": at, "cost_history": [entry, *(item.get("cost_history") or [])][:HISTORY]}
