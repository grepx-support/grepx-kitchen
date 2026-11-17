# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What the AI may know about a kitchen (grepx_bff.routers.ai): stock value by place, what runs low, lots expiring,
waste and production of the last days, food cost by day, open orders and bills, waiting approvals - and the morning
brief in plain words when AI is off."""
from __future__ import annotations

from datetime import date, timedelta

import grepx_contracts as gc


def money(v: float, cur: str) -> str:
    return f"{cur} {v:,.2f}".strip()


def _since(rows, days: int, today: date, field: str = "date"):
    start = (today - timedelta(days=days)).isoformat()
    return [r for r in rows if str(r.get(field) or "")[:10] >= start]


def facts(k) -> dict:
    today = date.today()
    cur = (k.one(gc.business.BUSINESSES, k.tenant) or {}).get("currency", "")
    items = {r["_key"]: r for r in k.rows(gc.item.ITEMS)}
    places = {key: p.get("name", "") for key, p in k.places().items()}
    value: dict[str, float] = {}
    for lv in k.rows(gc.stock.STOCK_LEVELS):
        it = items.get(lv.get("item_id"), {})
        value[places.get(lv.get("location_id"), "")] = value.get(places.get(lv.get("location_id"), ""), 0) + float(lv.get("qty") or 0) * float(it.get("cost") or 0)
    moves = _since(k.rows(gc.stock.STOCK_MOVEMENTS), 30, today)
    waste: dict[str, list] = {}
    made: dict[str, float] = {}
    for m in moves:
        name = items.get(m.get("item_id"), {}).get("name", m.get("item_id", ""))
        if m.get("kind") == "waste":
            w = waste.setdefault(name, [0.0, 0.0, m.get("reason", "")])
            w[0] += abs(float(m.get("qty") or 0))
            w[1] += abs(float(m.get("value") or 0))
        elif m.get("kind") == "produce":
            made[name] = made.get(name, 0) + float(m.get("qty") or 0)
    soon = (today + timedelta(days=3)).isoformat()
    expiring = [[items.get(l.get("item_id"), {}).get("name", ""), places.get(l.get("location_id"), ""), l.get("qty"), l.get("expiry")]
                for l in k.rows(gc.warehouse.LOTS) if l.get("open", True) and l.get("expiry") and str(l["expiry"]) <= soon and float(l.get("qty") or 0) > 0]
    days = sorted(k.rows(gc.costing.COST_DAYS), key=lambda d: d.get("date", ""))[-10:]
    orders = [p for p in k.rows(gc.purchase.PURCHASE_ORDERS) if p.get("state") not in ("received", "cancelled")]
    bills = [b for b in k.rows(gc.payables.BILLS) if b.get("state") in ("entered", "approved")]
    return {"currency": cur, "stock_value_by_place": {p: money(v, cur) for p, v in sorted(value.items(), key=lambda x: -x[1])},
            "items": len(items), "expiring_within_3_days": sorted(expiring, key=lambda e: str(e[3]))[:20],
            "waste_last_30_days": sorted(([n, round(q, 2), money(v, cur), r] for n, (q, v, r) in waste.items()), key=lambda w: w[2], reverse=True)[:15],
            "waste_total_30_days": money(sum(v for _, v, _ in waste.values()), cur),
            "made_last_30_days": sorted(([n, round(q, 1)] for n, q in made.items()), key=lambda x: -x[1])[:15],
            "food_cost_by_day": [[d.get("date"), d.get("sales"), d.get("cogs_pct")] for d in days],
            "open_purchase_orders": len(orders), "bills_to_pay": money(sum(float(b.get("total") or 0) for b in bills) / 100, cur),
            "approvals_waiting": sum(1 for a in k.rows(gc.approval.APPROVALS, state="pending")) if hasattr(gc, "approval") else 0}


def brief(k) -> tuple[dict, str]:
    data = facts(k)
    lines = []
    if data["expiring_within_3_days"]:
        first = data["expiring_within_3_days"][0]
        lines.append(f"{len(data['expiring_within_3_days'])} lots expire within 3 days - first {first[0]} at {first[1]} ({first[3]}).")
    lines.append(f"Waste in the last 30 days: {data['waste_total_30_days']}" + (f", most from {data['waste_last_30_days'][0][0]}." if data["waste_last_30_days"] else "."))
    if data["food_cost_by_day"] and data["food_cost_by_day"][-1][2] is not None:
        lines.append(f"Food cost on {data['food_cost_by_day'][-1][0]}: {data['food_cost_by_day'][-1][2]}% of sales.")
    if data["open_purchase_orders"]:
        lines.append(f"{data['open_purchase_orders']} purchase orders still to arrive; bills to pay {data['bills_to_pay']}.")
    if data["approvals_waiting"]:
        lines.append(f"{data['approvals_waiting']} approvals waiting.")
    return data, "\n".join(lines)
