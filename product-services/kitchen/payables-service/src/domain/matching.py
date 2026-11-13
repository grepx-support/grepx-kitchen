# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Three-way match: what was ordered (purchase order), what was received (the order's receipt) and what is billed, per item.
Quantities must not exceed what was received; prices may differ from the item's cost by the tolerance (%)."""
from __future__ import annotations

from decimal import Decimal

from dto import Issue, Match

TOLERANCE_PERCENT = Decimal(2)


def _per_item(lines: list[dict]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for l in lines or []:
        if l.get("item_id"):
            out[l["item_id"]] = out.get(l["item_id"], Decimal(0)) + Decimal(str(l.get("qty") or 0))
    return out


def match(bill_lines: list[dict], po: dict | None, costs: dict[str, int], tolerance=TOLERANCE_PERCENT) -> tuple[str, list[dict]]:
    """-> (Match, issues). costs = expected unit price per item, in cents."""
    if not po:
        return Match.NO_ORDER.value, []
    ordered, received = _per_item(po.get("lines")), _per_item(po.get("received"))
    issues = []
    for line in bill_lines:
        item = line.get("item_id")
        if not item:
            continue                                            # freight, surcharge ... not matched by item
        billed = Decimal(line["qty"])
        if item not in ordered:
            issues.append({"item_id": item, "issue": Issue.NOT_ORDERED.value})
        elif not po.get("received"):
            issues.append({"item_id": item, "issue": Issue.NOT_RECEIVED_YET.value})
        elif billed > received.get(item, Decimal(0)):
            issues.append({"item_id": item, "issue": Issue.MORE_THAN_RECEIVED.value, "billed": str(billed), "received": str(received.get(item, 0))})
        expected = costs.get(item)
        if expected and abs(line["unit_price"] - expected) * 100 > expected * Decimal(tolerance):
            issues.append({"item_id": item, "issue": Issue.PRICE_DIFFERS.value, "billed_price": line["unit_price"], "expected_price": expected})
    return (Match.CHECK.value if issues else Match.MATCHED.value), issues
