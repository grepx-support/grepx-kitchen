# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Step 5 - money: invoicing details, three wholesale customers, invoices in every state (paid, part paid, overdue,
draft) sent from the taco kitchen (so the tacos leave its stock) and supplier bills for the received orders (one matched and paid, one waiting for approval)."""
from __future__ import annotations

from datetime import date, timedelta

BILLING = {"legal_name": "Demo Taco Co Pty Ltd", "address": "12 Harbour Road\nSydney NSW 2000", "tax_label": "GST", "tax_number": "51 824 753 556",
           "tax_rate": 10, "payment_note": "Bank transfer to BSB 062-000, account 1234 5678, or PayID accounts@demo-taco.test. Please quote the invoice number."}
CUSTOMERS = [("Cafe Uno", "accounts@cafeuno.test", 14, "8 Pitt Street\nSydney NSW 2000"),
             ("Harbourside Catering", "ap@harbourside.test", 30, "2 Wharf Lane\nPyrmont NSW 2009"),
             ("Taco Tuesday Franchise", "finance@tacotuesday.test", 7, "77 King Street\nNewtown NSW 2042")]
INVOICES = [  # customer, days ago, lines [(item key or description, qty, price)], paid share (0..1, None = leave as draft)
    (0, 40, [("birria", 30, "38.50"), ("Delivery", 1, "15")], 1.0),
    (1, 20, [("pollo", 24, "36.00"), ("Catering staff (hours)", 6, "45")], 0.5),
    (2, 25, [("birria", 12, "38.50"), ("pollo", 12, "36.00")], 0.0),
    (0, 3, [("birria", 18, "38.50")], 0.0),
    (1, 0, [("pollo", 10, "36.00")], None),
]


def run(site, ids, say) -> None:
    item = ids["item"]
    site.patch("/setup/business", {"billing": BILLING}, "owner")
    cust = [site.post("/sales/customers", {"name": n, "email": e, "terms_days": t, "address": a}, "owner")["customer_id"] for n, e, t, a in CUSTOMERS]
    for who, ago, rows, paid in INVOICES:
        lines = [{"item_id": item[k], "qty": q, "unit_price": p} if k in item else {"description": k, "qty": q, "unit_price": p} for k, q, p in rows]
        inv = site.post("/sales/invoices", {"customer_id": cust[who], "tax_rate": BILLING["tax_rate"], "lines": lines,
                                            "location_id": ids["place"]["kit"]}, "owner")["invoice_id"]
        if paid is None:
            continue
        issued = site.post(f"/sales/invoices/{inv}/issue", {"issued": (date.today() - timedelta(days=ago)).isoformat()}, "owner")["invoice"]
        if paid:
            site.post(f"/sales/invoices/{inv}/pay", {"amount": f"{issued['total'] * paid / 100:.2f}", "method": "bank"}, "owner")
    say(f"{len(CUSTOMERS)} customers, {len(INVOICES)} invoices (paid, part paid, overdue, open, draft)")
    received = site.get("/bills", "owner")["to_bill"][:2]
    for n, order in enumerate(received):
        start = site.get(f"/bills/from-order/{order['po_id']}", "owner")
        bill = site.post("/bills", {"supplier_id": start["supplier_id"], "supplier_ref": f"SUP-{4100 + n}", "po_id": start["po_id"],
                                    "tax_rate": BILLING["tax_rate"], "lines": start["lines"]}, "owner")
        if n == 0:
            site.post(f"/bills/{bill['bill_id']}/approve", {}, "owner")
            site.post(f"/bills/{bill['bill_id']}/pay", {"amount": f"{bill['bill']['total'] / 100:.2f}"}, "owner")
    say(f"{len(received)} supplier bills from received orders")
