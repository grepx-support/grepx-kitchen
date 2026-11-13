# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every forecast action shares: the business it works for, today in its time zone, its products, places and
recent demand, and the accept / reject wrapper. A row of another business is treated as not there."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_service import RequestContext, state_of

from domain import daily_demand, forecast_one, series
from dto import ReasonCode, Table

HISTORY_DAYS = 56          # the forecast learns from the last eight weeks


class Stop(Exception):
    """A rejection with its reason."""


class Demand:
    """One business's products, places and what customers took of them."""

    def __init__(self, ctx, tenant: str):
        self.ctx, self.read, self.tenant = ctx, ctx.read, tenant
        self.business = ctx.read.accepted_one(gc.business.BUSINESSES, tenant) if tenant else None
        self._taken = None

    def today(self) -> date:
        try:
            zone = ZoneInfo((self.business or {}).get("timezone") or "UTC")
        except Exception:
            zone = timezone.utc
        return datetime.now(zone).date()

    def products(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.read.accepted(gc.item.ITEMS, tenant_id=self.tenant)
                if r.get("kind") == gc.item.ItemKind.FINISHED.value and r.get("active", True) is not False}

    def places(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.read.accepted(gc.business.LOCATIONS, tenant_id=self.tenant)}

    def taken(self) -> dict[tuple[str, str], dict[str, float]]:
        """(place, product) -> {date: qty} over the history window (read once per request)."""
        if self._taken is None:
            since = (self.today() - timedelta(days=HISTORY_DAYS)).isoformat()
            moves = [m for m in self.read.accepted(gc.stock.STOCK_MOVEMENTS, tenant_id=self.tenant) if m.get("date", "") >= since]
            self._taken = daily_demand(moves, set(self.products()))
        return self._taken

    def kept(self) -> list[dict]:
        return [state_of(r) for r in self.read.accepted(Table.FORECASTS.value, tenant_id=self.tenant)]

    def forecasts(self, days: list[date], method: str, location_id: str = "") -> list[dict]:
        """One row per place and product that has sold anything: its recent history and the forecast."""
        products, places, yesterday = self.products(), self.places(), self.today() - timedelta(days=1)
        if location_id and location_id not in places:
            raise Stop(ReasonCode.UNKNOWN_LOCATION)
        rows = []
        for (loc, item), by_day in sorted(self.taken().items()):
            if location_id and loc != location_id or item not in products or loc not in places:
                continue
            history = series(by_day, yesterday, HISTORY_DAYS)
            rows.append({"location_id": loc, "location_name": places[loc].get("name", ""), "item_id": item,
                         "name": products[item].get("name", ""), "unit": products[item].get("unit", ""),
                         "history": [{"date": d.isoformat(), "qty": round(q, 1)} for d, q in history[-28:]],
                         **forecast_one(history, days, method)})
        return rows


def run(ctx: RequestContext, body) -> None:
    tenant = ctx.text("tenant_id")
    try:
        if not tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        demand = Demand(ctx, tenant)
        if demand.business is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)
        out = body(demand)
    except (Stop, ValueError) as exc:
        return ctx.reject(exc.args[0])
    ctx.accept(out)
