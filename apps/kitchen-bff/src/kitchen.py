# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The signed-in business user: who, which business, what they may do - and commands that always carry the business.

Every kitchen request carries tenant_id = the user's business (from their login token, never from the client), and
every read filters by it, so one business never sees another's rows (BUS-05).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import grepx_contracts as gc
from fastapi import Depends

from grepx_bff.errors import ApiError
from grepx_bff.security import Principal, current_user, gateway
from grepx_bff.views import clean


@dataclass
class Kitchen:
    user: Principal
    gw: Any
    business: dict
    name: str

    @property
    def tenant(self) -> str:
        return self.user.tenant

    def can(self, perm: str) -> bool:
        return perm in self.user.perms or "*" in self.user.perms

    def cmd(self, table: str, service: str, fields: dict, key: Optional[str] = None) -> dict:
        return self.gw.command(table, service, {**fields, "tenant_id": self.tenant, "actor_id": self.user.user_id,
                                                "actor_name": self.name}, key=key).fields

    def rows(self, table: str, criteria: str = "", **eq) -> list[dict]:
        return self.gw.rows(table, criteria, tenant_id=self.tenant, **eq)

    def one(self, table: str, key: str) -> Optional[dict]:
        row = self.gw.one(table, key)
        return row if row and row.get("tenant_id") == self.tenant else None

    def location(self, key: str) -> dict:
        row = self.one(gc.business.LOCATIONS, key)
        if row is None:
            raise ApiError("UNKNOWN_LOCATION", 404)
        return row

    def items(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.rows(gc.item.ITEMS)}


def kitchen_user(user: Principal = Depends(current_user), gw=Depends(gateway)) -> Kitchen:
    if not user.tenant:
        raise ApiError("MISSING_TENANT", 403)
    business = gw.one(gc.business.BUSINESSES, user.tenant)
    if business is None:
        raise ApiError("UNKNOWN_BUSINESS", 403)
    person = gw.one(gc.people.PEOPLE, user.user_id) or {}
    return Kitchen(user, gw, business, person.get("name") or "")


def allow(*perms: str, module: str = ""):
    """The user holds one of perms (none given: any business user) and the module is switched on (BUS-03, ACC-02)."""
    def check(k: Kitchen = Depends(kitchen_user)) -> Kitchen:
        if module and not (k.business.get("modules") or {}).get(module, True):
            raise ApiError("MODULE_OFF", 403)
        if perms and not any(k.can(p) for p in perms):
            raise ApiError("FORBIDDEN", 403)
        return k
    return check


def named(rows: list[dict], items: dict[str, dict], places: dict[str, dict] | None = None) -> list[dict]:
    """Rows with the item (and location) names a screen shows."""
    out = []
    for r in rows:
        v = clean(r)
        item = items.get(r.get("item_id", ""), {})
        v.update({"item_name": item.get("name", r.get("item_id", "")), "unit": item.get("unit", ""), "item_kind": item.get("kind", "")})
        if places is not None:
            for field in ("location_id", "other_location_id"):
                if r.get(field):
                    v[field.replace("_id", "_name")] = places.get(r[field], {}).get("name", r[field])
        out.append(v)
    return out
