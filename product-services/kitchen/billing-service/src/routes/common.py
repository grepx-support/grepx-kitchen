# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""What every billing action shares: the business (tenant) it works for, its rows, today in its time zone, and the
accept / reject wrapper. A row of another business is treated as not there."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import grepx_contracts as gc
from grepx_service import RequestContext, state_of

from domain import clean_lines, fill_prices, tag_charges
from dto import ReasonCode, Table


class Stop(Exception):
    """A rejection with its reason."""


class Books:
    """One business's customers and invoices."""

    def __init__(self, ctx: RequestContext, tenant: str):
        self.ctx, self.read, self.tenant = ctx, ctx.read, tenant
        self.business = ctx.read.accepted_one(gc.business.BUSINESSES, tenant) if tenant else None

    def today(self) -> str:
        try:
            zone = ZoneInfo((self.business or {}).get("timezone") or "UTC")
        except Exception:
            zone = timezone.utc
        return datetime.now(zone).date().isoformat()

    def mine(self, table: str, key: str, reason) -> dict:
        row = self.read.accepted_one(table, key) if key else None
        if row is None or row.get("tenant_id") != self.tenant:
            raise Stop(reason)
        return state_of(row)

    def customer(self, key: str) -> dict:
        return self.mine(Table.CUSTOMERS.value, key, ReasonCode.UNKNOWN_CUSTOMER)

    def customers(self) -> list[dict]:
        return [{**state_of(r), "customer_id": r["_key"]} for r in self.read.accepted(Table.CUSTOMERS.value, tenant_id=self.tenant)]

    def invoice(self, key: str) -> dict:
        return self.mine(Table.INVOICES.value, key, ReasonCode.UNKNOWN_INVOICE)

    def quote(self, key: str) -> dict:
        return self.mine(Table.QUOTES.value, key, ReasonCode.UNKNOWN_QUOTE)

    def quotes(self) -> list[dict]:
        return [state_of(r) for r in self.read.accepted(Table.QUOTES.value, tenant_id=self.tenant)]

    def location(self, key: str) -> dict:
        return self.mine(gc.business.LOCATIONS, key, ReasonCode.UNKNOWN_LOCATION)

    def invoices(self) -> list[dict]:
        return [state_of(r) for r in self.read.accepted(Table.INVOICES.value, tenant_id=self.tenant)]

    def breaks(self) -> dict[str, list]:
        return {r["_key"]: r.get("breaks") or [] for r in self.read.accepted(Table.PRICE_BREAKS.value, tenant_id=self.tenant)}

    def lines(self, raw: list, customer: dict | None) -> list[dict]:
        """Document lines with the customer's prices filled in where none was typed, charges tagged, amounts worked out."""
        items = self.items()
        filled = fill_prices(raw, items, (customer or {}).get("pricing"), self.breaks())
        return tag_charges(filled, clean_lines(filled, items))

    def items(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.read.accepted(gc.item.ITEMS, tenant_id=self.tenant)}

    def save(self, table: str, key: str, row: dict) -> dict:
        row = {**row, "tenant_id": self.tenant}
        self.ctx.emitter.submit(table, key, "ACCEPTED", row)
        return row


def run(ctx: RequestContext, body) -> None:
    tenant = ctx.text("tenant_id")
    try:
        if not tenant:
            raise Stop(ReasonCode.MISSING_TENANT)
        books = Books(ctx, tenant)
        if books.business is None:
            raise Stop(ReasonCode.UNKNOWN_BUSINESS)
        out = body(books)
    except (Stop, ValueError) as exc:
        return ctx.reject(exc.args[0])
    ctx.accept(out)
