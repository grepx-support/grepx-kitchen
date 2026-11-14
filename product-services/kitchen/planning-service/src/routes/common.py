# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every recommendation reads: the business, its settings, items, stock, movements - one business only."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_service import RequestContext

from domain import Usage
from dto import ReasonCode


class Stop(Exception):
    pass


class View:
    def __init__(self, ctx: RequestContext):
        self.ctx = ctx
        self.tenant = ctx.text("tenant_id")
        if not self.tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        self.business = ctx.read.accepted_one(gc.business.BUSINESSES, self.tenant)
        if self.business is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)
        self.settings = self.business.get("settings") or {}

    def today(self) -> date:
        try:
            return datetime.now(ZoneInfo(self.business.get("timezone") or "UTC")).date()
        except Exception:
            return datetime.now(timezone.utc).date()

    def location(self, field: str = "location_id") -> dict:
        key = self.ctx.text(field)
        row = self.ctx.read.accepted_one(gc.business.LOCATIONS, key) if key else None
        if row is None or row.get("tenant_id") != self.tenant:
            raise Stop(ReasonCode.UNKNOWN_LOCATION)
        return row

    def locations(self) -> list[dict]:
        return [r for r in self.ctx.read.accepted(gc.business.LOCATIONS, tenant_id=self.tenant) if r.get("active", True)]

    def items(self, *kinds: str) -> list[dict]:
        rows = [r for r in self.ctx.read.accepted(gc.item.ITEMS, tenant_id=self.tenant) if r.get("active", True)]
        return [r for r in rows if not kinds or r.get("kind") in kinds]

    def usage(self) -> Usage:
        weeks = int(self.ctx.get("weeks") or self.settings.get("target_weeks") or 2)
        since = (self.today() - timedelta(days=7 * max(1, min(3, weeks)) + 1)).isoformat()
        moves = self.ctx.read.accepted(gc.stock.STOCK_MOVEMENTS, f"date >= '{since}'", tenant_id=self.tenant)
        first = self.ctx.read.accepted(gc.stock.STOCK_MOVEMENTS, tenant_id=self.tenant) if moves else []
        oldest = min((m["date"] for m in first if m.get("date")), default=None)
        if oldest and oldest < since:          # history older than the window: the window is full
            moves = [*moves, {"date": since, "kind": "marker"}]
        return Usage(moves, self.today(), weeks)

    def stock(self) -> dict[str, dict[str, float]]:
        """location -> item -> qty."""
        out: dict[str, dict[str, float]] = defaultdict(dict)
        for r in self.ctx.read.accepted(gc.stock.STOCK_LEVELS, tenant_id=self.tenant):
            out[r["location_id"]][r["item_id"]] = r.get("qty", 0)
        return out

    def safety(self) -> float:
        return float(self.settings.get("safety_pct", 10))


def total(by_location: dict, only=None) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for loc, items in by_location.items():
        if only is None or loc in only:
            for iid, q in items.items():
                out[iid] += q
    return dict(out)


def run(ctx: RequestContext, body) -> None:
    try:
        result = body(View(ctx))
    except Stop as stop:
        return ctx.reject(stop.args[0])
    ctx.accept({"plan": result})
