# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Employees in bulk (employee-service SAVE): matched by email, else by name, so importing again updates them."""
from __future__ import annotations

import grepx_contracts as gc

from .base import Column, Importer, by_name, find


class Employees(Importer):
    kind, title = "employees", "Employees"
    notes = ("One row per person. Someone already there with the same email (or, without an email, the same name) is updated.",
             "Home site must be one of your places. Pay basis: monthly (a salary) or hourly.")
    columns = (Column("Name", "name", True, example="Meera Iyer"), Column("Email", "email", example="meera@example.test", help="matched to update"),
               Column("Phone", "phone", example="+919800000111"), Column("Position", "position", example="Cook"), Column("Department", "department", example="Kitchen"),
               Column("Home site", "home_site", example="Central kitchen - Powai", help="a place's name"),
               Column("Start date", "start_date", kind="date", example="2026-04-01"),
               Column("Pay basis", "basis", example="monthly", help="monthly / hourly"), Column("Pay rate", "rate", kind="number", example="28000",
               help="a month's salary, or pay per hour"))

    def context(self, k) -> dict:
        people, places = k.rows(gc.employee.EMPLOYEES), k.rows(gc.business.LOCATIONS)
        return {"by_email": by_name(people, "email"), "by_name": by_name(people), "places": by_name(places),
                "place_names": {p["_key"]: p.get("name", "") for p in places}}

    def prepare(self, v, ctx):
        place = find(ctx["places"], v["home_site"], "place")
        basis = (v["basis"] or "monthly").lower()
        if basis not in ("monthly", "hourly"):
            raise ValueError("Pay basis must be monthly or hourly")
        old = (ctx["by_email"].get((v["email"] or "").lower()) if v["email"] else None) or (None if v["email"] else ctx["by_name"].get(v["name"].lower()))
        body = {f: v[f] for f in ("name", "email", "phone", "position", "department", "start_date") if v[f] is not None}
        body |= {**({"home_site": place["_key"], "sites": [place["_key"]]} if place else {}), **({"employee_id": old["_key"]} if old else {}),
                 **({"pay": {"basis": basis, "rate": v["rate"]}} if v["rate"] is not None else {})}
        return body, "update" if old else "create", v["name"]

    def save(self, k, body):
        k.cmd(gc.employee.REQUESTS, gc.employee.SERVICE, {"action": "SAVE", **body})

    def export(self, k, ctx):
        pn = ctx["place_names"]
        return [[e.get("name"), e.get("email"), e.get("phone"), e.get("position"), e.get("department"), pn.get(e.get("home_site"), ""), e.get("start_date"),
                 (e.get("pay") or {}).get("basis", ""), (e.get("pay") or {}).get("rate", "")]
                for e in sorted(k.rows(gc.employee.EMPLOYEES), key=lambda e: e.get("name", "").lower()) if e.get("active", True)]
