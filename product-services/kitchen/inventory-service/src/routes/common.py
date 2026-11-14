# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every inventory action shares: the business, its rows, and today in the business's time zone."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_service import RequestContext, state_of

from dto import ReasonCode


class Stop(Exception):
    """A rejection with its reason."""


class Stock:
    """One business's stock, as inventory control reads it."""

    def __init__(self, read, tenant: str):
        self.read, self.tenant = read, tenant
        self.business = read.accepted_one(gc.business.BUSINESSES, tenant) if tenant else None

    def today(self) -> str:
        try:
            zone = ZoneInfo((self.business or {}).get("timezone") or "UTC")
        except Exception:
            zone = timezone.utc
        return datetime.now(zone).date().isoformat()

    def mine(self, table: str, key: str, reason: str) -> dict:
        row = self.read.accepted_one(table, key) if key else None
        if row is None or row.get("tenant_id") != self.tenant:
            raise Stop(reason)
        return row

    def levels(self, location_id: str = "") -> list[dict]:
        rows = self.read.accepted(gc.stock.STOCK_LEVELS, tenant_id=self.tenant)
        return [r for r in rows if not location_id or r.get("location_id") == location_id]

    def items(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.read.accepted(gc.item.ITEMS, tenant_id=self.tenant)}

    def costs(self) -> dict[str, float]:
        return {k: float(v.get("cost") or 0) for k, v in self.items().items()}

    def lots(self) -> list[dict]:
        return [{**l, "lot_id": l["_key"]} for l in self.read.accepted(gc.warehouse.LOTS, tenant_id=self.tenant) if l.get("qty", 0) > 0]

    def locations(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.read.accepted(gc.business.LOCATIONS, tenant_id=self.tenant)}


def open_stock(ctx: RequestContext) -> Stock:
    tenant = ctx.text("tenant_id")
    if not tenant:
        raise Stop(ReasonCode.MISSING_TENANT)
    stock = Stock(ctx.read, tenant)
    if stock.business is None:
        raise Stop(ReasonCode.UNKNOWN_BUSINESS)
    return stock


def run(ctx: RequestContext, body) -> None:
    try:
        out = body(open_stock(ctx))
    except Stop as stop:
        return ctx.reject(stop.args[0])
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept(out)


__all__ = ["Stock", "Stop", "open_stock", "run", "state_of"]
