# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SNAPSHOT - keep today's and tomorrow's forecast for every place and product, once per day (a day already kept is
left as it was, so it stays the forecast made before the day started)."""
from datetime import timedelta

from grepx_service import RequestContext

from domain import AUTO
from dto import Table
from .common import Demand, run


def keep(demand: Demand) -> list[str]:
    """Store the days not kept yet; returns the dates stored."""
    today, stored = demand.today(), []
    have = {r["date"] for r in demand.kept()}
    for day in (today, today + timedelta(days=1)):
        if day.isoformat() in have:
            continue
        rows = demand.forecasts([day], AUTO)
        lines = [{"location_id": r["location_id"], "item_id": r["item_id"], "qty": r["forecast"][0]["qty"], "method": r["method"]} for r in rows]
        demand.ctx.emitter.submit(Table.FORECASTS.value, f"{demand.tenant}:{day.isoformat()}", "ACCEPTED",
                                  {"tenant_id": demand.tenant, "date": day.isoformat(), "lines": lines})
        stored.append(day.isoformat())
    return stored


def handle(ctx: RequestContext) -> None:
    run(ctx, lambda demand: {"kept": keep(demand)})
