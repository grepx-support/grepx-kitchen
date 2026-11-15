# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The signed-in business user: who, which business, what they may do - and commands that always carry the business.

Every kitchen request carries tenant_id = the user's business (from their login token, never from the client), and
every read filters by it, so one business never sees another's rows (BUS-05).
"""
from __future__ import annotations

from dataclasses import dataclass

import grepx_contracts as gc

from grepx_bff.business import Access, Business, listed, signed_in  # noqa: F401 (listed: kitchen routers import it from here)
from grepx_bff.views import clean


@dataclass
class Kitchen(Business):
    """The shared business user plus the kitchen's own lookups."""

    def items(self) -> dict[str, dict]:
        return {r["_key"]: r for r in self.rows(gc.item.ITEMS)}


kitchen_user = signed_in(Kitchen)
ACCESS = Access(kitchen_user)
allow, feature_on = ACCESS.allow, ACCESS.feature_on


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
