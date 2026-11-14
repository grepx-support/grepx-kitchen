# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The four recommendations. Quantities are rounded up to whole units; a person always decides the final number (R6)."""
from __future__ import annotations

import math


def up(value: float) -> float:
    if value <= 0:
        return 0
    return math.ceil(round(value, 6))


def _r(value: float | None, places: int = 2):
    return None if value is None else round(value, places)


def production_target(finished: list[dict], recipes: dict, usage, on_hand: dict, safety_pct: float, manual: dict,
                      ingredient_stock: dict, names: dict) -> dict:
    """R5 / KIT-03..05: finished goods to make this week, batches when the batch output is known, ingredients to buy.

    target = weekly usage x (1 + safety) + event extra (Q12) - stock on hand anywhere in the business; a manual target
    for the week replaces the calculation (KIT-10)."""
    lines, need = [], {}
    for item in finished:
        iid = item["_key"]
        weekly = usage.weekly(iid)
        man = manual.get(iid) or {}
        if man.get("qty") is not None:
            target, source = float(man["qty"]), "manual"
        elif weekly is None:
            target, source = None, "no_history"
        else:
            target = up(weekly * (1 + safety_pct / 100) + float(man.get("extra") or 0) - on_hand.get(iid, 0))
            source = "usage"
        recipe = recipes.get(iid)
        batches = None
        if target is not None and recipe and float(recipe.get("batch_output") or 0) > 0:
            batches = math.ceil(target / float(recipe["batch_output"])) if target > 0 else 0
            for ing in recipe.get("ingredients") or []:
                need[ing["item_id"]] = need.get(ing["item_id"], 0) + batches * float(ing["qty"])
        lines.append({"item_id": iid, "name": item.get("name", ""), "unit": item.get("unit", ""), "weekly_usage": _r(weekly),
                      "on_hand": on_hand.get(iid, 0), "extra": man.get("extra") or 0, "target": target, "batches": batches,
                      "batch_output": (recipe or {}).get("batch_output"), "source": source})
    ingredients = [{"item_id": iid, "name": names.get(iid, {}).get("name", iid), "unit": names.get(iid, {}).get("unit", ""),
                    "needed": _r(qty), "on_hand": ingredient_stock.get(iid, 0), "to_buy": up(qty - ingredient_stock.get(iid, 0))}
                   for iid, qty in sorted(need.items())]
    return {"lines": lines, "ingredients": ingredients, "has_history": usage.has_history, "history_days": usage.days}


def warehouse_out(items: list[dict], usage, location_id: str, at_location: dict, at_holding: dict, days_of_cover: int) -> dict:
    """R4 / INV-02: enough at the location for its days of cover: daily usage there x days - what it already has."""
    lines = []
    for item in items:
        iid = item["_key"]
        daily = usage.daily(iid, location_id)
        if not daily:
            continue
        suggest = up(daily * days_of_cover - at_location.get(iid, 0))
        if suggest > 0:
            lines.append({"item_id": iid, "name": item.get("name", ""), "unit": item.get("unit", ""), "daily_usage": _r(daily),
                          "at_location": at_location.get(iid, 0), "at_holding": at_holding.get(iid, 0), "suggested": suggest})
    return {"lines": lines, "days_of_cover": days_of_cover, "has_history": usage.has_history, "history_days": usage.days}


def warehouse_in(items: list[dict], usage, at_holding: dict, elsewhere: dict, safety_pct: float) -> dict:
    """INV-05: what the holding place needs for the coming week - the demand of every location - beyond the stock already
    held anywhere in the business."""
    lines = []
    for item in items:
        iid = item["_key"]
        weekly = usage.weekly(iid)
        if not weekly:
            continue
        need = up(weekly * (1 + safety_pct / 100) - at_holding.get(iid, 0) - elsewhere.get(iid, 0))
        lines.append({"item_id": iid, "name": item.get("name", ""), "unit": item.get("unit", ""), "kind": item.get("kind", ""),
                      "weekly_usage": _r(weekly), "at_holding": at_holding.get(iid, 0), "elsewhere": elsewhere.get(iid, 0), "needed": need})
    return {"lines": [l for l in lines if l["needed"] > 0], "has_history": usage.has_history, "history_days": usage.days}


def reorder(items: list[dict], usage, on_hand: dict, on_order: dict, safety_pct: float, previous: dict,
            large_change_pct: float) -> dict:
    """R6 / ORD-02 / ORD-04: weekly usage x (1 + safety) - stock in the business - already on order, per supplier;
    next to the previous recommendation, flagged when it moved more than large_change_pct."""
    lines = []
    for item in items:
        iid = item["_key"]
        weekly = usage.weekly(iid)
        if weekly is None:
            continue
        qty = up(weekly * (1 + safety_pct / 100) - on_hand.get(iid, 0) - on_order.get(iid, 0))
        before = previous.get(iid)
        large = False
        if before is not None and (before or qty):
            base = before if before else qty
            large = abs(qty - before) / base * 100 > large_change_pct
        if qty > 0 or before:
            lines.append({"item_id": iid, "name": item.get("name", ""), "unit": item.get("unit", ""), "supplier_id": item.get("supplier_id", ""),
                          "weekly_usage": _r(weekly), "on_hand": on_hand.get(iid, 0), "on_order": on_order.get(iid, 0),
                          "recommended": qty, "previous": before, "large_change": large})
    return {"lines": lines, "has_history": usage.has_history, "history_days": usage.days}
