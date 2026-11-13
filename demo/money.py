# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 5 - money: invoicing details, three wholesale customers, invoices in every state (paid, part paid, overdue,
draft) sent from the kitchen (so the food leaves its stock) and supplier bills for the received orders (one matched and paid, one waiting for approval)."""
from __future__ import annotations

from datetime import date, timedelta


def run(site, d, ids, say) -> None:
    item = ids["item"]
    if site.get("/sales", "owner")["customers"]:            # run before: do not add the customers and invoices twice
        return say("money: customers already there - skipped")
    site.patch("/setup/business", {"billing": d.BILLING}, "owner")
    cust = [site.post("/sales/customers", {"name": n, "email": e, "terms_days": t, "address": a}, "owner")["customer_id"] for n, e, t, a in d.CUSTOMERS]
    for who, ago, rows, paid in d.INVOICES:
        lines = [{"item_id": item[k], "qty": q, "unit_price": p} if k in item else {"description": k, "qty": q, "unit_price": p} for k, q, p in rows]
        inv = site.post("/sales/invoices", {"customer_id": cust[who], "tax_rate": d.BILLING["tax_rate"], "lines": lines,
                                            "location_id": ids["place"]["kit"]}, "owner")["invoice_id"]
        if paid is None:
            continue
        issued = site.post(f"/sales/invoices/{inv}/issue", {"issued": (date.today() - timedelta(days=ago)).isoformat()}, "owner")["invoice"]
        if paid:
            site.post(f"/sales/invoices/{inv}/pay", {"amount": f"{issued['total'] * paid / 100:.2f}", "method": "bank"}, "owner")
    say(f"{len(d.CUSTOMERS)} customers, {len(d.INVOICES)} invoices (paid, part paid, overdue, open, draft)")
    received = site.get("/bills", "owner")["to_bill"][:2]
    for n, order in enumerate(received):
        start = site.get(f"/bills/from-order/{order['po_id']}", "owner")
        bill = site.post("/bills", {"supplier_id": start["supplier_id"], "supplier_ref": d.BILL_REF.format(n=4100 + n), "po_id": start["po_id"],
                                    "tax_rate": d.BILLING["tax_rate"], "lines": start["lines"]}, "owner")
        if n == 0:
            site.post(f"/bills/{bill['bill_id']}/approve", {}, "owner")
            site.post(f"/bills/{bill['bill_id']}/pay", {"amount": f"{bill['bill']['total'] / 100:.2f}"}, "owner")
    say(f"{len(received)} supplier bills from received orders")
