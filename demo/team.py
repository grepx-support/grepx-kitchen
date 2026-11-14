# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Demo team: employees across the outlets (d.TEAM), documents (one expired, one expiring), this week's roster
(published at the kitchen), one open shift, and clock PINs 1234."""
from __future__ import annotations

from datetime import date, timedelta


def run(site, d, ids: dict, say) -> None:
    team = getattr(d, "TEAM", [])
    if not team:
        return
    people = {}
    for name, position, home, more, basis, rate in team:
        sites = [ids["place"][home]] + [ids["place"][m] for m in more]
        people[name] = site.post("/team", {"name": name, "position": position, "home_site": sites[0], "sites": sites, "start_date": "2025-04-01",
                                           "pay": {"basis": basis, "rate": rate, "weekly_hours": 48}}, "owner")["employee_id"]
        site.post(f"/team/{people[name]}/pin", {"pin": "1234"}, "owner")
    for name, kind, ends in getattr(d, "TEAM_DOCS", []):
        site.post(f"/team/{people[name]}/documents", {"kind": kind, "expires_on": (date.today() + timedelta(days=ends)).isoformat()}, "owner")
    monday = date.today() - timedelta(days=date.today().weekday())
    shifts = 0
    for i in range(6):
        for name, (place, start, end) in getattr(d, "TEAM_SHIFTS", {}).items():
            if (i + len(name)) % 7:
                site.post("/roster/shifts", {"site_id": ids["place"][place], "employee_id": people[name], "date": (monday + timedelta(days=i)).isoformat(),
                                             "start": start, "end": end, "break_min": 45}, "owner")
                shifts += 1
    site.post("/roster/shifts", {"site_id": ids["place"][d.SELLERS[0]], "date": (monday + timedelta(days=5)).isoformat(), "start": "18:00", "end": "23:00",
                                 "role": "Extra hand"}, "owner")
    kitchen = next(k for k, _, kind, *_ in d.PLACES if kind == "kitchen")
    site.post("/roster/publish", {"site_id": ids["place"][kitchen], "week": monday.isoformat()}, "owner")
    say(f"{len(people)} people across the outlets, {shifts} shifts this week, clock PIN 1234")
