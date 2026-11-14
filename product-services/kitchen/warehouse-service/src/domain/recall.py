# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Recall: from a lot (or every lot with a lot code), everywhere it went - places it was sent to, dishes it was cooked
into, customers it was sold to, what was thrown away - and what is still on the shelf; and, for something made, the
ingredient lots it came from. Pure."""
from __future__ import annotations

OUT_TO_CUSTOMER = ("sale",)


def start(lots: list[dict], code: str) -> list[dict]:
    """The lots a recall starts from: this lot id, or every lot with this lot code (case and spaces ignored)."""
    want = code.strip().lower()
    return [l for l in lots if l.get("lot_id") == code or (want and str(l.get("lot_code") or "").strip().lower() == want)]


def children(lot: dict, lots: list[dict]) -> list[dict]:
    """Lots this one became: the same goods arrived somewhere else, or something made from it."""
    return [l for l in lots if l.get("parent") == lot["lot_id"] or lot["lot_id"] in (l.get("made_from") or [])]


def trace(first: list[dict], lots: list[dict]) -> dict:
    """Follow the lots forward. Returns every lot reached (with depth and how it was reached), every use, the open stock to
    pull, the customers to call, and the ingredient lots the starting lots were made from."""
    by_id = {l["lot_id"]: l for l in lots}
    seen, queue, reached = set(), [(l, 0, "start") for l in first], []
    while queue:
        lot, depth, how = queue.pop(0)
        if lot["lot_id"] in seen:
            continue
        seen.add(lot["lot_id"])
        reached.append({**lot, "depth": depth, "how": how})
        for c in children(lot, lots):
            queue.append((c, depth + 1, "made into" if lot["lot_id"] in (c.get("made_from") or []) else "moved to"))
    uses = [{**u, "lot_id": l["lot_id"], "item_id": l.get("item_id"), "lot_code": l.get("lot_code", "")} for l in reached for u in l.get("uses") or []]
    customers: dict[str, dict] = {}
    for u in uses:
        if u.get("kind") in OUT_TO_CUSTOMER:
            key = u.get("customer_id") or u.get("customer_name") or u.get("ref") or "unknown"
            c = customers.setdefault(key, {"customer_id": u.get("customer_id", ""), "name": u.get("customer_name", "") or key, "qty": 0.0, "invoices": []})
            c["qty"] = round(c["qty"] + float(u.get("qty") or 0), 4)
            if u.get("invoice_number") and u["invoice_number"] not in c["invoices"]:
                c["invoices"].append(u["invoice_number"])
    on_hand = [l for l in reached if float(l.get("qty") or 0) > 0]
    origins = [by_id[i] for l in first for i in l.get("made_from") or [] if i in by_id]
    return {"lots": reached, "uses": sorted(uses, key=lambda u: u.get("date", "")), "on_hand": on_hand,
            "customers": sorted(customers.values(), key=lambda c: -c["qty"]), "made_from": origins,
            "totals": {"lots": len(reached), "on_hand": round(sum(float(l["qty"]) for l in on_hand), 4), "customers": len(customers),
                       "sold": round(sum(c["qty"] for c in customers.values()), 4)}}
