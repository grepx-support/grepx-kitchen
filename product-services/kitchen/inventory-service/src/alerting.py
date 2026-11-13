# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Find today's alerts for one business, keep each once, and tell its owners once a day (email, WhatsApp, SMS - logged
only until the business connects a provider)."""
from __future__ import annotations

import grepx_contracts as gc
from grepx_service import notify, now_iso

from domain import alert_key, alerts
from dto import Table

LABEL = {"low": "below minimum", "negative": "below zero - count it", "expiring": "expiring soon", "expired": "expired"}


def owners(read, tenant: str) -> list[dict]:
    """The owners of the business (their staff role is <tenant>.owner) with their contact details."""
    out = []
    for access in read.accepted(gc.access.USER_ACCESS):
        if access.get("staff_role_id") == f"{tenant}.owner":
            person = read.accepted_one(gc.people.PEOPLE, access["_key"])
            if person:
                out.append(person)
    return out


def check(stock, emitter, link: str = "") -> list[dict]:
    """Write today's new alerts; notify the owners when there are new ones. Returns the new alerts."""
    day = stock.today()
    pars = {(p["location_id"], p["item_id"]): p for p in stock.read.accepted(Table.PAR_LEVELS.value, tenant_id=stock.tenant)}
    items, places = stock.items(), stock.locations()
    new = []
    for a in alerts(day, stock.levels(), pars, stock.lots()):
        key = alert_key(stock.tenant, day, a)
        if stock.read.one(Table.ALERTS.value, key):
            continue
        row = {**a, "tenant_id": stock.tenant, "date": day, "state": "open", "created_at": now_iso(),
               "item_name": items.get(a["item_id"], {}).get("name", ""), "unit": items.get(a["item_id"], {}).get("unit", ""),
               "location_name": places.get(a["location_id"], {}).get("name", "")}
        emitter.submit(Table.ALERTS.value, key, "ACCEPTED", row)
        new.append(row)
    if new:
        summary = "\n".join(f"- {r['item_name']} at {r['location_name']}: {LABEL[r['kind']]}" for r in new[:12])
        for person in owners(stock.read, stock.tenant):
            notify(emitter, "stock_alert", email=person.get("email", ""), phone=person.get("phone", ""),
                   channels=["email", "whatsapp", "sms"], ref=f"alerts-{stock.tenant}-{day}-{len(new)}", tenant_id=stock.tenant,
                   user_id=person.get("_key", ""), values={"first_name": (person.get("name") or "").split(" ")[0], "count": len(new),
                                                          "summary": summary, "link": link})
    return new
