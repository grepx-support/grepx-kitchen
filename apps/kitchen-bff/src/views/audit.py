# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The audit trail: every change anyone asked for in the business - who, when, what, and whether it was done or refused
(and why). It is read from the request rows each service answers through Nexus, so nothing can change without a line
here. Questions that only read (reports, forecasts) are left out."""

AREAS = {"business": "Setup", "item": "Items", "stock": "Stock", "purchase": "Orders", "planning": "Kitchen", "closing": "Closing",
         "costing": "Costs", "warehouse": "Warehouse", "delivery": "Delivery", "inventory": "Inventory", "billing": "Invoices",
         "payables": "Supplier bills"}
READS = {"planning:PRODUCTION_TARGET", "planning:REORDER", "planning:WAREHOUSE_IN", "planning:WAREHOUSE_OUT", "costing:SUMMARY", "inventory:VALUATION", "inventory:ANALYSIS",
         "inventory:CHECK_ALERTS", "billing:SUMMARY", "billing:MONTHLY", "billing:MARGINS", "billing:STATEMENT", "payables:SUMMARY",
         "payables:MONTHLY"}
SHOWN = ("qty", "number", "name", "note", "reason_text", "amount", "ref", "kind", "date", "channels", "state")
HIDDEN = {"action", "actor_id", "actor_name", "tenant_id", "status", "reason", "detail", "occurred_at", "transaction_id", "application",
          "username", "to_service", "trace_id", "cause", "version", "_key", "_version"}


def words(action: str) -> str:
    return action.replace("_", " ").capitalize()


def what(row: dict, names: dict[str, str]) -> str:
    """A short line of the main details, with ids turned into names."""
    bits = [names.get(str(row.get(f)), "") for f in ("item_id", "location_id", "supplier_id", "customer_id") if row.get(f)]
    bits += [f"{f.replace('_', ' ')} {row[f]}" for f in SHOWN if row.get(f) not in (None, "", [])]
    lines = row.get("lines")
    if isinstance(lines, list) and lines:
        bits.append(f"{len(lines)} line{'s' if len(lines) != 1 else ''}")
    return " · ".join(b for b in bits if b)[:200]


def entries(by_area: dict[str, list[dict]], names: dict[str, str]) -> list[dict]:
    out = []
    for area, rows in by_area.items():
        for r in rows:
            action = str(r.get("action") or "")
            if not action or f"{area}:{action}" in READS or r.get("status") in ("NEW", "CLAIMED"):
                continue
            out.append({"id": r["_key"], "at": r.get("occurred_at", ""), "area": AREAS.get(area, area), "action": words(action),
                        "who": r.get("actor_name") or ("the app" if not r.get("actor_id") else r.get("actor_id")),
                        "done": r.get("status") == "ACCEPTED", "why": r.get("detail") or r.get("reason") or "",
                        "what": what(r, names),
                        "fields": {k: v for k, v in r.items() if k not in HIDDEN and not k.startswith("_") and v not in (None, "", [], {})}})
    return sorted(out, key=lambda e: e["at"], reverse=True)
