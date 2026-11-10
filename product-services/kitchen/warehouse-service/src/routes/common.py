# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every warehouse action shares: the business, its own rows, and turning a failed check into a rejection."""
from __future__ import annotations

import grepx_contracts as gc
from grepx_service import RequestContext, state_of

from dto import ReasonCode, Table


class Stop(Exception):
    """A rejection with its reason."""


class Floor:
    """One business's warehouse for one request."""

    def __init__(self, ctx: RequestContext):
        self.ctx = ctx
        self.tenant = ctx.text("tenant_id")
        if not self.tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        if ctx.read.accepted_one(gc.business.BUSINESSES, self.tenant) is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)

    def mine(self, table: str, key: str, reason: str) -> dict:
        """A row of this business (another business's row is treated as not there)."""
        row = self.ctx.read.accepted_one(table, key) if key else None
        if row is None or row.get("tenant_id") != self.tenant:
            raise Stop(reason)
        return row

    def location(self, field: str = "location_id") -> dict:
        return self.mine(gc.business.LOCATIONS, self.ctx.text(field), ReasonCode.UNKNOWN_LOCATION)

    def items(self, lines: list[dict]) -> dict[str, dict]:
        return {l["item_id"]: self.mine(gc.item.ITEMS, l["item_id"], ReasonCode.UNKNOWN_ITEM) for l in lines}

    def open_lots(self, location_id: str, item_id: str) -> list[dict]:
        return [{**l, "lot_id": l["_key"]} for l in self.ctx.read.accepted(Table.LOTS.value, tenant_id=self.tenant,
                                                                           location_id=location_id, item_id=item_id) if l.get("qty", 0) > 0]

    def save(self, table: str, key: str, row: dict) -> dict:
        self.ctx.emitter.submit(table, key, "ACCEPTED", row)
        return row

    def who(self) -> dict:
        return {"by": self.ctx.text("actor_id"), "by_name": self.ctx.text("actor_name")}


def run(ctx: RequestContext, body) -> None:
    """Run body(floor) -> fields to accept with; any failed check rejects with its reason."""
    try:
        out = body(Floor(ctx))
    except Stop as stop:
        return ctx.reject(stop.args[0])
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept(out)


__all__ = ["Floor", "Stop", "run", "state_of"]
