# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Invoice rules: lines and totals, numbering, issue and due dates, payments, credit notes, the state a reader sees.
Pure functions over plain dicts - all money in cents (grepx_money)."""
from __future__ import annotations

from datetime import date, timedelta

from grepx_money import cents, document_lines as clean_lines, priced  # noqa: F401  (re-exported: the service's line rules)

from dto import InvoiceState as S, Kind, Method, ReasonCode

PREFIX = {Kind.INVOICE.value: "INV", Kind.CREDIT.value: "CN"}


def next_number(kind: str, year: int, taken: list[str]) -> str:
    """Gapless per kind and year: INV-2026-0001, INV-2026-0002 ... (CN- for credit notes)."""
    prefix = f"{PREFIX[kind]}-{year}-"
    seq = max((int(n[len(prefix):]) for n in taken if n.startswith(prefix) and n[len(prefix):].isdigit()), default=0)
    return f"{prefix}{seq + 1:04d}"


def due_on(issued: str, terms_days: int) -> str:
    return (date.fromisoformat(issued) + timedelta(days=int(terms_days))).isoformat()


def balance(inv: dict) -> int:
    return inv.get("total", 0) - inv.get("paid", 0) - inv.get("credited", 0)


def pay(inv: dict, amount, on: str, method: str, reference: str, by: str) -> dict:
    """Record a (part) payment; paid in full -> PAID. More than is still owed is refused."""
    if inv.get("state") != S.ISSUED.value:
        raise ValueError(ReasonCode.NOT_OPEN)
    value = cents(amount)
    if value <= 0:
        raise ValueError(ReasonCode.INVALID_AMOUNT)
    if value > balance(inv):
        raise ValueError(ReasonCode.MORE_THAN_DUE)
    if method not in {m.value for m in Method}:
        raise ValueError(ReasonCode.INVALID_METHOD)
    _check_date(on)
    payments = [*(inv.get("payments") or []), {"amount": value, "date": on, "method": method, "reference": reference[:60], "by": by}]
    out = {**inv, "payments": payments, "paid": inv.get("paid", 0) + value}
    return settle(out)


def settle(inv: dict) -> dict:
    """Nothing left to pay -> PAID."""
    return {**inv, "state": S.PAID.value} if inv.get("state") == S.ISSUED.value and balance(inv) <= 0 else inv


def void(inv: dict) -> dict:
    if inv.get("state") not in (S.DRAFT.value, S.ISSUED.value):
        raise ValueError(ReasonCode.NOT_OPEN)
    if inv.get("paid") or inv.get("credited"):
        raise ValueError(ReasonCode.HAS_PAYMENTS)
    return {**inv, "state": S.VOID.value}


def credit_against(inv: dict, credit_total: int) -> dict:
    """A credit note reduces what the customer owes on the invoice it corrects; never below zero."""
    if inv.get("state") != S.ISSUED.value or inv.get("kind") != Kind.INVOICE.value:
        raise ValueError(ReasonCode.NOT_OPEN)
    if credit_total > balance(inv):
        raise ValueError(ReasonCode.MORE_THAN_DUE)
    return settle({**inv, "credited": inv.get("credited", 0) + credit_total})


def status(inv: dict, today: str) -> str:
    """What a reader sees: draft, overdue, part paid, open, paid, void (stored state + dates + money)."""
    state = inv.get("state")
    if state != S.ISSUED.value:
        return state
    if inv.get("due") and inv["due"] < today:
        return "overdue"
    return "part paid" if inv.get("paid") or inv.get("credited") else "open"


BUCKETS = (("current", None), ("1-30", 30), ("31-60", 60), ("61-90", 90), ("90+", 10 ** 6))


def ageing(invoices: list[dict], today: str) -> dict[str, int]:
    """What is still owed, by how many days past due (cents)."""
    out = {name: 0 for name, _ in BUCKETS}
    t = date.fromisoformat(today)
    for inv in invoices:
        if inv.get("state") != S.ISSUED.value or inv.get("kind") != Kind.INVOICE.value:
            continue
        late = (t - date.fromisoformat(inv["due"])).days if inv.get("due") else 0
        name = "current" if late <= 0 else next(n for n, limit in BUCKETS[1:] if late <= limit)
        out[name] += balance(inv)
    return out


def _check_date(on: str) -> None:
    try:
        date.fromisoformat(on)
    except (TypeError, ValueError):
        raise ValueError(ReasonCode.INVALID_DATE)
