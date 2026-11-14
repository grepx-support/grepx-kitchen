# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The books for an accounting system, for a date range: issued invoices and credit notes, approved supplier bills and
returns, and payments both ways - as a balanced journal (any system), or as Xero / QuickBooks import files. The double
entry itself is grepx_money.ledger; this collects the documents and lays the rows out per format (strategy per format)."""
from __future__ import annotations

from grepx_money import from_cents, ledger

FORMATS = {"journal": "General journal (any accounting system)", "trial": "Trial balance", "xero_sales": "Xero - sales invoices",
           "xero_bills": "Xero - bills", "qb_invoices": "QuickBooks - invoices", "qb_bills": "QuickBooks - bills"}


def within(day: str, start: str, end: str) -> bool:
    return bool(day) and (not start or day >= start) and (not end or day <= end)


class Books:
    """The business's documents for [start, end]."""

    def __init__(self, invoices: list[dict], bills: list[dict], start: str, end: str, accounts: dict | None = None):
        self.start, self.end, self.acc = start, end, ledger.Accounts.of(accounts)
        self.invoices = [i for i in invoices if i.get("state") in ("issued", "paid")]
        self.bills = [b for b in bills if b.get("state") in ("approved", "paid")]

    def journal(self) -> list[dict]:
        rows: list[dict] = []
        for i in self.invoices:
            credit = i.get("kind") == "credit"
            if within(i.get("issued", ""), self.start, self.end):
                rows += ledger.sale({"date": i["issued"], "ref": i["number"], "text": f"{'Credit note' if credit else 'Invoice'} {i['number']} - {i.get('customer_name', '')}",
                                     "total": i["total"], "tax": i.get("tax", 0), "charges": i.get("charges", 0)}, self.acc, credit_note=credit)
            for p in i.get("payments") or []:
                if within(p.get("date", ""), self.start, self.end):
                    rows += ledger.received({"date": p["date"], "ref": i["number"], "text": f"Payment from {i.get('customer_name', '')}", "amount": p["amount"]}, self.acc)
        for b in self.bills:
            ref, who = b.get("supplier_ref", ""), b.get("supplier_name", "")
            if within(b.get("bill_date", ""), self.start, self.end):
                rows += ledger.purchase({"date": b["bill_date"], "ref": ref, "text": f"Bill {ref} - {who}", "total": b["total"], "tax": b.get("tax", 0),
                                         "landed": b.get("landed_on_bill", 0)}, self.acc)
            for r in b.get("returns") or []:
                if within(r.get("date", ""), self.start, self.end):
                    rows += ledger.supplier_credit({"date": r["date"], "ref": f"{ref} return", "text": f"Returned to {who}", "total": r["credit"], "tax": r.get("tax", 0)}, self.acc)
            for p in b.get("payments") or []:
                if within(p.get("date", ""), self.start, self.end):
                    rows += ledger.paid({"date": p["date"], "ref": ref, "text": f"Paid {who}", "amount": p["amount"]}, self.acc)
        return sorted(rows, key=lambda r: (r["date"], r["ref"]))

    # ---- one table per format: (headings, rows) ----
    def table(self, fmt: str) -> tuple[list[str], list[list]]:
        return getattr(self, f"_{fmt}")()

    def _journal(self):
        return (["Date", "Reference", "Description", "Account", "Debit", "Credit"],
                [[r["date"], r["ref"], r["description"], r["account"], from_cents(r["debit"]) if r["debit"] else "", from_cents(r["credit"]) if r["credit"] else ""]
                 for r in self.journal()])

    def _trial(self):
        return (["Account", "Debit", "Credit", "Balance"],
                [[a["account"], from_cents(a["debit"]), from_cents(a["credit"]), from_cents(a["balance"])] for a in ledger.trial_balance(self.journal())])

    def _lines(self, doc: dict) -> list[dict]:
        return doc.get("lines") or []

    def _xero_sales(self):
        rows = [[i.get("customer_name", ""), i["number"], i["issued"], i.get("due", i["issued"]), l.get("description", ""), l.get("qty", 1),
                 from_cents(l.get("unit_price", 0)), l.get("discount") or "", self.acc.charges if l.get("charge") else self.acc.sales, f"{i.get('tax_rate', 0)}%",
                 "Credit note" if i.get("kind") == "credit" else "Invoice"]
                for i in self.invoices if within(i.get("issued", ""), self.start, self.end) for l in self._lines(i)]
        return (["*ContactName", "*InvoiceNumber", "*InvoiceDate", "*DueDate", "*Description", "*Quantity", "*UnitAmount", "Discount", "*AccountCode", "*TaxType", "Type"], rows)

    def _xero_bills(self):
        rows = [[b.get("supplier_name", ""), b.get("supplier_ref", ""), b["bill_date"], b.get("due", b["bill_date"]), l.get("description", ""), l.get("qty", 1),
                 from_cents(l.get("unit_price", 0)), self.acc.purchases, f"{b.get('tax_rate', 0)}%"]
                for b in self.bills if within(b.get("bill_date", ""), self.start, self.end) for l in self._lines(b)]
        return (["*ContactName", "*InvoiceNumber", "*InvoiceDate", "*DueDate", "*Description", "*Quantity", "*UnitAmount", "*AccountCode", "*TaxType"], rows)

    def _qb_invoices(self):
        rows = [[i["number"], i.get("customer_name", ""), i["issued"], i.get("due", i["issued"]), l.get("description", ""), l.get("description", ""), l.get("qty", 1),
                 from_cents(l.get("unit_price", 0)), from_cents(l.get("amount", 0)), "TAX" if float(i.get("tax_rate") or 0) else "NON"]
                for i in self.invoices if i.get("kind") != "credit" and within(i.get("issued", ""), self.start, self.end) for l in self._lines(i)]
        return (["InvoiceNo", "Customer", "InvoiceDate", "DueDate", "Item(Product/Service)", "ItemDescription", "ItemQuantity", "ItemRate", "ItemAmount", "ItemTaxCode"], rows)

    def _qb_bills(self):
        rows = [[b.get("supplier_ref", ""), b.get("supplier_name", ""), b["bill_date"], b.get("due", b["bill_date"]), self.acc.purchases, l.get("description", ""),
                 from_cents(l.get("amount", 0))]
                for b in self.bills if within(b.get("bill_date", ""), self.start, self.end) for l in self._lines(b)]
        return (["Bill No", "Supplier", "Bill Date", "Due Date", "Account", "Line Description", "Line Amount"], rows)
