# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Demo funds (d.FUNDS): partners' capital with promises (one overdue, one still to come), money in - some paid in
another currency at its rate - money put to the places (named like them, so Funds links each place's real costs), a
bank loan with interest and repayments, and a fund kept in a foreign currency. Parties have an email, so their
statements can be sent. The Funds page then shows suggestions, the runway, the forecast and the balance sheet."""
from __future__ import annotations

from datetime import date, timedelta


def move(site, fund_id: str, parties: dict, m: tuple, day) -> None:
    """m: (kind, amount, party, days ago, due-in-days for a promise | use name, optional {currency, rate, ref, note})."""
    what, amount, who, days_ago, extra, *more = m
    body = {"kind": what, "amount": amount, "party_id": parties.get(who, ""), "date": day(days_ago), **(more[0] if more else {})}
    if what == "commit":
        body["due"] = day(extra)
    elif extra:
        body["purpose"] = extra
    site.post(f"/funds/{fund_id}/entries", body, "owner")


def run(site, d, ids: dict, say) -> None:
    funds = getattr(d, "FUNDS", [])
    if not funds:
        return
    parties = {}
    for name, kind, *contact in getattr(d, "FUND_PARTIES", []):
        email, phone = (contact + ["", ""])[:2]
        parties[name] = site.post("/funds/parties", {"name": name, "kind": kind, "email": email, "phone": phone}, "owner")["party_id"]
    day = lambda n: (date.today() - timedelta(days=n)).isoformat()  # noqa: E731
    moved = 0
    for name, kind, target, rate, moves, *options in funds:
        fund = site.post("/funds", {"name": name, "kind": kind, "target": target, "rate_pct": rate, **(options[0] if options else {})}, "owner")
        for m in moves:
            move(site, fund["fund_id"], parties, m, day)
            moved += 1
        if name in getattr(d, "FUND_PLANS", {}):
            site.put(f"/funds/{fund['fund_id']}/plan", d.FUND_PLANS[name], "owner")
    say(f"{len(funds)} funds, {len(parties)} parties, {moved} movements (one promise overdue, money in two currencies)")
