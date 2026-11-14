# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Demo funds (d.FUNDS): partners' capital with promises (one overdue), money in, money put to the outlets, a bank
loan with interest and repayments - so the Funds page shows what was brought in, what is pending and where it went."""
from __future__ import annotations

from datetime import date, timedelta


def run(site, d, ids: dict, say) -> None:
    funds = getattr(d, "FUNDS", [])
    if not funds:
        return
    parties = {name: site.post("/funds/parties", {"name": name, "kind": kind}, "owner")["party_id"] for name, kind in getattr(d, "FUND_PARTIES", [])}
    day = lambda n: (date.today() - timedelta(days=n)).isoformat()  # noqa: E731
    moved = 0
    for name, kind, target, rate, moves in funds:
        fund = site.post("/funds", {"name": name, "kind": kind, "target": target, "rate_pct": rate}, "owner")
        for what, amount, who, days_ago, extra in moves:
            site.post(f"/funds/{fund['fund_id']}/entries", {"kind": what, "amount": amount, "party_id": parties.get(who, ""), "date": day(days_ago),
                                                            **({"due": day(extra)} if what == "commit" else {"purpose": extra} if extra else {})}, "owner")
            moved += 1
        if name in getattr(d, "FUND_PLANS", {}):
            site.put(f"/funds/{fund['fund_id']}/plan", d.FUND_PLANS[name], "owner")
    say(f"{len(funds)} funds, {len(parties)} parties, {moved} movements (one promise overdue)")
