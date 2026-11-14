# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""VALUATION - what the stock is worth; ANALYSIS - ABC by usage value, days of cover, waste by reason (read only)."""
from datetime import date, timedelta

import grepx_contracts as gc
from grepx_service import RequestContext

from domain import abc, consumption, cover, valuation, waste_by_reason
from .common import run


def value(ctx: RequestContext) -> None:
    def body(stock):
        lines = valuation(stock.levels(ctx.text("location_id")), stock.costs(), stock.lots())
        return {"lines": lines, "total": round(sum(l["value"] for l in lines), 2), "lot_total": round(sum(l["lot_value"] for l in lines), 2)}
    run(ctx, body)


def analyse(ctx: RequestContext) -> None:
    def body(stock):
        days = max(7, min(90, int(ctx.get("days") or 30)))
        since = (date.fromisoformat(stock.today()) - timedelta(days=days)).isoformat()
        moves = [m for m in ctx.read.accepted(gc.stock.STOCK_MOVEMENTS, tenant_id=stock.tenant) if m.get("date", "") >= since]
        places, items = stock.locations(), stock.items()
        used = consumption(moves, {k for k, v in places.items() if v.get("kind") == "kitchen"},
                           {k for k, v in items.items() if v.get("kind") == "finished"})
        on_hand: dict[str, float] = {}
        for lv in stock.levels():
            on_hand[lv["item_id"]] = on_hand.get(lv["item_id"], 0.0) + float(lv.get("qty") or 0)
        classes, covers = abc(used), cover(on_hand, used, days)
        rows = [{"item_id": i, "name": it.get("name", ""), "unit": it.get("unit", ""), "kind": it.get("kind", ""),
                 "used_qty": round(used.get(i, {}).get("qty", 0.0), 2), "used_value": round(used.get(i, {}).get("value", 0.0), 2),
                 "class": classes.get(i, "C"), "on_hand": round(on_hand.get(i, 0.0), 2), "days_of_cover": covers.get(i)}
                for i, it in items.items() if it.get("active", True)]
        return {"days": days, "since": since, "items": sorted(rows, key=lambda r: -r["used_value"]), "waste": waste_by_reason(moves, stock.costs())}
    run(ctx, body)
