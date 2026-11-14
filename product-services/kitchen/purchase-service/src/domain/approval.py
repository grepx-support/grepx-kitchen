# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Order approval: an order worth more than the amount the owner set needs their yes before it goes to the supplier.
An approval holds for the value approved - an order changed to cost more needs approving again."""
from __future__ import annotations

PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"


def order_value(lines: list[dict], items: dict[str, dict]) -> float:
    """Qty x the item's cost, in the business currency."""
    return round(sum(float(l["qty"]) * float(items.get(l["item_id"], {}).get("cost") or 0) for l in lines), 2)


def approval_for(value: float, limit: float, current: dict | None) -> dict | None:
    """None when no approval is needed; else the approval record (kept when still covering this value)."""
    if not limit or value <= float(limit):
        return None
    if current and current.get("state") == APPROVED and value <= float(current.get("value") or 0):
        return current
    return {"state": PENDING, "value": value, "limit": float(limit)}


def may_send(approval: dict | None) -> bool:
    return approval is None or approval.get("state") == APPROVED


def decide(approval: dict | None, yes: bool, by: str, note: str, at: str) -> dict:
    if not approval or approval.get("state") != PENDING:
        raise ValueError("NOTHING_TO_APPROVE")
    if not yes and not note.strip():
        raise ValueError("NOTE_REQUIRED")
    return {**approval, "state": APPROVED if yes else REJECTED, "by": by, "note": note.strip()[:300], "at": at}
