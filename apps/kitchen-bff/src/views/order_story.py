# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""A purchase order's story for the screens: where it stands (on order, received, billed, paid, cancelled), its events in
time order (made, sent, received, billed, approved, paid / cancelled) and each line ordered against received. Pure."""
from __future__ import annotations

STAGES = ("on_order", "received", "billed", "paid", "cancelled")


def stage(po: dict, bills: list[dict]) -> str:
    """The furthest step this order reached; its bills decide billed / paid (a voided bill does not count)."""
    if po.get("state") == "cancelled":
        return "cancelled"
    live = [b for b in bills if b.get("state") != "void"]
    if live and all(b.get("state") == "paid" for b in live):
        return "paid"
    if live:
        return "billed"
    return "received" if po.get("state") == "received" else "on_order"


def _event(at: str, kind: str, title: str, who: str = "", detail: str = "") -> dict:
    return {"at": at or "", "kind": kind, "title": title, "who": who or "", "detail": detail}


def timeline(po: dict, bills: list[dict], money=lambda cents: f"{cents / 100:.2f}") -> list[dict]:
    """Every event of the order and its supplier bills, oldest first."""
    out = [_event(po.get("created_at"), "made", f"Order {po.get('number', '')} made", po.get("created_by_name"),
                  f"{len(po.get('lines') or [])} line(s) for {po.get('supplier_name', '')}")]
    for s in po.get("sent") or []:
        out.append(_event(s.get("at"), "sent", "Sent to the supplier", s.get("by"), " · ".join(s.get("channels") or [])))
    if po.get("received_at"):
        changed = sum(1 for l in line_view(po, {}) if l["difference"])
        out.append(_event(po["received_at"], "received", "Received into stock", po.get("received_by_name"),
                          f"{changed} line(s) differ from the order" if changed else "as ordered"))
    if po.get("state") == "cancelled":
        out.append(_event(po.get("cancelled_at") or po.get("updated_at"), "cancelled", "Cancelled", po.get("cancelled_by_name")))
    for b in bills:
        ref = b.get("supplier_ref") or b.get("bill_id", "")
        out.append(_event(b.get("entered_at"), "billed", f"Supplier bill {ref}", b.get("entered_by"), f"total {money(b.get('total') or 0)} · match: {b.get('match') or '-'}"))
        if b.get("approved_by"):
            out.append(_event(b.get("approved_at") or b.get("entered_at"), "approved", f"Bill {ref} approved", b.get("approved_by"), b.get("approval_note") or ""))
        for p in b.get("payments") or []:
            on = p.get("at") or p.get("date") or ""          # a payment keeps only its date: it sorts at the end of that day
            out.append(_event(on if "T" in on or not on else f"{on}T23:59:59", "paid", f"Paid {money(p.get('amount') or 0)}", p.get("by"), p.get("method") or ""))
        if b.get("state") == "void":
            out.append(_event(b.get("updated_at") or b.get("entered_at"), "void", f"Bill {ref} voided"))
    return sorted(out, key=lambda e: e["at"])


def line_view(po: dict, items: dict[str, dict], show_cost: bool = False) -> list[dict]:
    """Each line: name, unit, ordered, received (when it was), the difference and - for people who see costs - its value."""
    got = {l["item_id"]: float(l["qty"]) for l in po.get("received") or []}
    rows = []
    for l in po.get("lines") or []:
        item = items.get(l["item_id"], {})
        ordered = float(l["qty"])
        received = got.get(l["item_id"]) if po.get("received") else None
        row = {"item_id": l["item_id"], "name": l.get("item_name") or item.get("name", l["item_id"]), "unit": l.get("unit") or item.get("unit", ""),
               "ordered": ordered, "received": received, "difference": round(received - ordered, 3) if received is not None and received != ordered else 0}
        if show_cost:
            cost = float(item.get("cost") or 0)
            row.update({"unit_cost": cost, "value": round((received if received is not None else ordered) * cost, 2)})
        rows.append(row)
    return rows
