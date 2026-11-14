# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Telling the owners of a business when a supplier's price jumps (email / WhatsApp, in the business's own words -
Outbox -> What goes out). Once per bill and set of jumps."""
from __future__ import annotations

import hashlib

import grepx_contracts as gc
from grepx_service import notify


def owners(read, tenant: str) -> list[dict]:
    """The owners of the business (staff role <tenant>.owner) with their contact details."""
    found = (read.accepted_one(gc.people.PEOPLE, a["_key"]) for a in read.accepted(gc.access.USER_ACCESS) if a.get("staff_role_id") == f"{tenant}.owner")
    return [p for p in found if p]


def tell_owners(ap, bill: dict, jumps: list[dict]) -> None:
    if not jumps:
        return
    cur = ap.business.get("currency", "")
    summary = "\n".join(f"- {j['description']}: {cur} {j['from'] / 100:,.2f} -> {j['to'] / 100:,.2f} per {j['unit'] or 'unit'} (+{j['pct']}%)" for j in jumps[:12])
    ref = hashlib.sha1(f"{bill['bill_id']}|{summary}".encode()).hexdigest()[:16]
    for person in owners(ap.read, ap.tenant):
        notify(ap.ctx.emitter, "price_jump", email=person.get("email", ""), phone=person.get("phone", ""), channels=["email", "whatsapp"],
               ref=f"price-{ref}", tenant_id=ap.tenant, user_id=person.get("_key", ""),
               values={"first_name": (person.get("name") or "").split(" ")[0], "supplier": bill.get("supplier_name", ""), "count": len(jumps),
                       "summary": summary, "bill": bill.get("supplier_ref", "")})
