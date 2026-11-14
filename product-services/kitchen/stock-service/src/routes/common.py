# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every stock action shares: the business, its locations and items, and writing levels + movements."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_service import RequestContext

from domain import apply, clean_lines, level_key
from dto import ReasonCode, Table


class Stop(Exception):
    """A rejection with its reason (raised by the checks, turned into ctx.reject by run())."""


class Book:
    """One business's view for one request: checks references and records the change."""

    def __init__(self, ctx: RequestContext):
        self.ctx = ctx
        self.tenant = ctx.text("tenant_id")
        if not self.tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        self.business = ctx.read.accepted_one(gc.business.BUSINESSES, self.tenant)
        if self.business is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)

    def location(self, field: str = "location_id") -> dict:
        key = self.ctx.text(field)
        row = self.ctx.read.accepted_one(gc.business.LOCATIONS, key) if key else None
        if row is None or row.get("tenant_id") != self.tenant or not row.get("active", True):
            raise Stop(ReasonCode.UNKNOWN_LOCATION)
        return row

    def items(self, lines: list[dict]) -> dict[str, dict]:
        found = {}
        for line in lines:
            row = self.ctx.read.accepted_one(gc.item.ITEMS, line["item_id"])
            if row is None or row.get("tenant_id") != self.tenant:
                raise Stop(ReasonCode.UNKNOWN_ITEM)
            found[line["item_id"]] = row
        return found

    def lines(self, allow_zero: bool = False, allow_empty: bool = False) -> list[dict]:
        if allow_empty and not self.ctx.get("lines"):
            return []
        try:
            return clean_lines(self.ctx.get("lines") or [], allow_zero)
        except ValueError as exc:
            raise Stop(str(exc))

    def today(self) -> str:
        try:
            zone = ZoneInfo(self.business.get("timezone") or "UTC")
        except Exception:
            zone = timezone.utc
        return datetime.now(zone).date().isoformat()

    def record(self, steps: list[dict], items: dict[str, dict], extra: dict | None = None) -> list[dict]:
        """Apply the steps to the current levels; write the new levels and one movement per step."""
        keys = sorted({level_key(s["location_id"], s["item_id"]) for s in steps})
        current = {}
        for key in keys:
            row = self.ctx.read.accepted_one(Table.STOCK_LEVELS.value, key)
            current[key] = (row or {}).get("qty", 0)
        after, moves = apply(current, steps)
        stamp, day = datetime.now(timezone.utc).isoformat(timespec="microseconds"), self.ctx.text("date") or self.today()   # orders same-second moves
        who = {"user_id": self.ctx.text("actor_id"), "user_name": self.ctx.text("actor_name")}
        for key in keys:
            location_id, item_id = key.split(":", 1)
            self.ctx.emitter.submit(Table.STOCK_LEVELS.value, key, "ACCEPTED",
                                    {"tenant_id": self.tenant, "location_id": location_id, "item_id": item_id, "qty": after[key],
                                     "updated_at": stamp})
        out = []
        for n, move in enumerate(moves):
            cost = float(items[move["item_id"]].get("cost") or 0)
            row = {"movement_id": f"{self.ctx.key}-{n}", "tenant_id": self.tenant, **move, "unit_cost": cost,
                   "value": round(move["qty"] * cost, 4), "at": stamp, "date": day, "request_id": self.ctx.key,
                   "note": self.ctx.text("note"), "ref": self.ctx.text("ref"), **who, **(extra or {})}
            self.ctx.emitter.submit(Table.STOCK_MOVEMENTS.value, row["movement_id"], "ACCEPTED", row)
            out.append(row)
        return out


def run(ctx: RequestContext, body) -> None:
    """Run an action body(book) -> movements; reject with the reason any check raised."""
    try:
        book = Book(ctx)
        moves = body(book)
    except Stop as stop:
        return ctx.reject(stop.args[0])
    ctx.accept({"movements": len(moves), "changes": [{k: m[k] for k in ("location_id", "item_id", "kind", "qty", "before", "after")}
                                                    for m in moves]})
