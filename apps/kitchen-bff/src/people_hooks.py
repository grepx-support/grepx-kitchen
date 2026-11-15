# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""How the shared people and funds features (grepx_bff.people) reach the kitchen's own books (costing-service):

- locking a payroll month puts each outlet's labour cost (pay + employer contributions) into Costs for that month;
- a fund's use named like one of the outlets shows that outlet's real costs and EBITDA (the Costs page's numbers)."""
from __future__ import annotations

import grepx_contracts as gc

from grepx_bff.business import Business
from grepx_bff.people import last_months, months_back

CATEGORIES = (("ingredient_cost", "Ingredients"), ("labour", "Labour"), ("rent", "Rent"), ("other", "Other costs"))


def labour_into_costs(k: Business, month: str, done: dict) -> None:
    """Set each outlet's labour cost for the locked month (rent and other costs stay as they were)."""
    places = set(k.places())
    for site, cost in done["cost_by_site"].items():
        if site not in places:
            continue
        now = next(iter(k.rows(gc.costing.OVERHEADS, location_id=site, month=month)), {})
        k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SET_OVERHEAD", "location_id": site, "month": month, "labour": cost,
                                                        "rent": now.get("rent", 0), "other": now.get("other", 0)})


def summaries(k: Business, location_ids: list[str], months: list[str]) -> dict[str, dict[str, dict]]:
    """{location_id: {month: costing summary}} in one request (not one per place and month)."""
    if not location_ids:
        return {}
    return k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SUMMARIES", "months": months, "location_ids": location_ids})["summaries"]


def place_ids(k: Business) -> dict[str, str]:
    return {r.get("name", ""): key for key, r in k.places().items()}


class OutletCosts:
    """FundCosts from the Costs page: per outlet and month, ingredients / labour / rent / other, and net profit."""

    def spending(self, k: Business, purposes: set[str], n: int = 6) -> dict[str, list[dict]]:
        places = place_ids(k)
        used = sorted(purposes & set(places))
        grid = summaries(k, [places[p] for p in used], months_back(n))
        out: dict[str, list[dict]] = {}
        for purpose in used:
            for m, s in grid.get(places[purpose], {}).items():
                out.setdefault(purpose, []).extend({"month": m, "category": label, "amount": round(float(s.get(f) or 0) * 100)}
                                                   for f, label in CATEGORIES if s.get(f))
        return out

    def actuals(self, k: Business, uses: list[str]) -> dict[str, list[float]]:
        """Each use that is an outlet: its EBITDA for each of the last three months that had sales."""
        places = place_ids(k)
        pairs = [(u, places[u]) for u in uses if places.get(u)]
        grid = summaries(k, sorted({loc for _, loc in pairs}), last_months())
        out: dict[str, list[float]] = {}
        for purpose, loc in pairs:
            for s in grid.get(loc, {}).values():
                if s.get("sales") and s.get("net_profit") is not None:
                    out.setdefault(purpose, []).append(float(s["net_profit"]))
        return out
