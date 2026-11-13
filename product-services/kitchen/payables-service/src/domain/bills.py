# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Bill rules: duplicate check, due date, approval, payments, void, what is due when. Pure; money in cents."""
from __future__ import annotations

from datetime import date, timedelta

from grepx_money import cents

from dto import BillState as S, Match, ReasonCode

METHODS = ("bank", "cash", "card", "paynow", "cheque", "other")


def check_dates(*days: str) -> None:
    for d in days:
        try:
            date.fromisoformat(d)
        except (TypeError, ValueError):
            raise ValueError(ReasonCode.INVALID_DATE)


def due_from(bill_date: str, terms_days: int) -> str:
    return (date.fromisoformat(bill_date) + timedelta(days=int(terms_days))).isoformat()


def is_duplicate(supplier_id: str, supplier_ref: str, others: list[dict], own_key: str = "") -> bool:
    ref = supplier_ref.strip().lower()
    return any(b.get("supplier_id") == supplier_id and str(b.get("supplier_ref", "")).strip().lower() == ref
               and b.get("state") != S.VOID.value and b.get("bill_id") != own_key for b in others)


def balance(bill: dict) -> int:
    return bill.get("total", 0) - bill.get("paid", 0)


def approve(bill: dict, note: str, by: str) -> dict:
    """A bill that does not match needs a note saying why it is fine to pay."""
    if bill.get("state") != S.ENTERED.value:
        raise ValueError(ReasonCode.NOT_ENTERED)
    if bill.get("match") == Match.CHECK.value and not note.strip():
        raise ValueError(ReasonCode.NOTE_REQUIRED)
    return {**bill, "state": S.APPROVED.value, "approved_by": by, "approval_note": note.strip()[:300]}


def pay(bill: dict, amount, on: str, method: str, reference: str, by: str) -> dict:
    if bill.get("state") != S.APPROVED.value:
        raise ValueError(ReasonCode.NOT_APPROVED)
    value = cents(amount)
    if value <= 0:
        raise ValueError(ReasonCode.INVALID_AMOUNT)
    if value > balance(bill):
        raise ValueError(ReasonCode.MORE_THAN_DUE)
    if method not in METHODS:
        raise ValueError(ReasonCode.INVALID_METHOD)
    check_dates(on)
    out = {**bill, "paid": bill.get("paid", 0) + value,
           "payments": [*(bill.get("payments") or []), {"amount": value, "date": on, "method": method, "reference": reference[:60], "by": by}]}
    return {**out, "state": S.PAID.value} if balance(out) <= 0 else out


def void(bill: dict) -> dict:
    if bill.get("state") not in (S.ENTERED.value, S.APPROVED.value):
        raise ValueError(ReasonCode.NOT_ENTERED)
    if bill.get("paid"):
        raise ValueError(ReasonCode.HAS_PAYMENTS)
    return {**bill, "state": S.VOID.value}


def due_buckets(bills: list[dict], today: str) -> dict[str, int]:
    """Still to pay: overdue, due this week, later (cents)."""
    out = {"overdue": 0, "this_week": 0, "later": 0}
    week = (date.fromisoformat(today) + timedelta(days=7)).isoformat()
    for b in bills:
        if b.get("state") not in (S.ENTERED.value, S.APPROVED.value):
            continue
        key = "overdue" if b["due"] < today else "this_week" if b["due"] <= week else "later"
        out[key] += balance(b)
    return out
