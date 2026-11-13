# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""FORECAST (read only) - per place and product: the last four weeks and the forecast for the next `days` (default 7)
with the method used (`method`: auto = the most accurate for each product) and its tested error; the totals per
product across places (what the kitchen must make); and how the kept forecasts did against what really sold."""
from grepx_service import RequestContext

from domain import AUTO, METHODS, days_ahead, kept_accuracy
from .common import run


def totals(rows: list[dict]) -> list[dict]:
    out: dict[str, dict] = {}
    for r in rows:
        t = out.setdefault(r["item_id"], {"item_id": r["item_id"], "name": r["name"], "unit": r["unit"], "total": 0.0, "first_day": 0.0})
        t["total"] = round(t["total"] + r["total"], 1)
        t["first_day"] = round(t["first_day"] + (r["forecast"][0]["qty"] if r["forecast"] else 0), 1)
    return sorted(out.values(), key=lambda t: -t["total"])


def handle(ctx: RequestContext) -> None:
    def body(demand):
        today = demand.today()
        days = days_ahead(ctx.get("days"), today)
        rows = demand.forecasts(days, ctx.text("method") or AUTO, ctx.text("location_id"))
        return {"today": today.isoformat(), "days": [d.isoformat() for d in days], "rows": rows, "products": totals(rows),
                "methods": [{"key": m.key, "label": m.label} for m in METHODS.values()],
                "accuracy": kept_accuracy(demand.kept(), demand.taken(), today.isoformat())[-14:]}
    run(ctx, body)
