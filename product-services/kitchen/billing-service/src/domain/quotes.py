# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Catering quotations: quote -> order -> invoice. Pure rules - which move is allowed from which state, the event
details, numbering, how long a quote is valid, what a reader sees, and the invoice an order becomes."""
from __future__ import annotations

import re
from datetime import date, timedelta

from dto import InvoiceState, Kind, QuoteState as Q, ReasonCode

MOVES = {                                       # action -> states it may start from
    "save": {Q.DRAFT, Q.SENT},
    "send": {Q.DRAFT, Q.SENT},
    "accept": {Q.DRAFT, Q.SENT},
    "decline": {Q.DRAFT, Q.SENT},
    "cancel": {Q.DRAFT, Q.SENT, Q.ORDERED},
    "invoice": {Q.ORDERED},
}
VALID_DAYS = 14
TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def may(action: str, quote: dict) -> None:
    if Q(quote.get("state", Q.DRAFT.value)) not in MOVES[action]:
        raise ValueError(ReasonCode.WRONG_STATE)


def numbered(prefix: str, year: int, taken: list[str]) -> str:
    """Gapless per prefix and year: Q-2026-0001 for quotes, SO-2026-0001 for orders."""
    start = f"{prefix}-{year}-"
    seq = max((int(n[len(start):]) for n in taken if n.startswith(start) and n[len(start):].isdigit()), default=0)
    return f"{start}{seq + 1:04d}"


def clean_event(raw: dict) -> dict:
    """The event the food is for: date (required), start time, venue, number of guests."""
    try:
        on = date.fromisoformat(str(raw.get("event_date") or "")).isoformat()
        guests = int(float(raw.get("guests") or 0))
    except (TypeError, ValueError):
        raise ValueError(ReasonCode.INVALID_EVENT)
    at = str(raw.get("event_time") or "")
    if (at and not TIME.match(at)) or not 0 <= guests <= 100000:
        raise ValueError(ReasonCode.INVALID_EVENT)
    return {"event_date": on, "event_time": at, "venue": " ".join(str(raw.get("venue") or "").split())[:200], "guests": guests,
            "event_name": " ".join(str(raw.get("event_name") or "").split())[:120]}


def valid_until(on: str, days) -> str:
    try:
        n = int(days if days not in (None, "") else VALID_DAYS)
    except (TypeError, ValueError):
        raise ValueError(ReasonCode.INVALID_DATE)
    if not 1 <= n <= 365:
        raise ValueError(ReasonCode.INVALID_DATE)
    return (date.fromisoformat(on) + timedelta(days=n)).isoformat()


def check_open(quote: dict, today: str) -> None:
    """A sent quote past its date can no longer be accepted (send it again to renew it)."""
    if quote.get("state") == Q.SENT.value and (quote.get("valid_until") or "9999") < today:
        raise ValueError(ReasonCode.QUOTE_EXPIRED)


def view_status(quote: dict, today: str) -> str:
    """draft, sent, expired, ordered, invoiced, declined, cancelled."""
    if quote.get("state") == Q.SENT.value and (quote.get("valid_until") or "9999") < today:
        return "expired"
    return quote.get("state", Q.DRAFT.value)


def per_guest(quote: dict) -> int:
    """Total per guest in cents (0 without guests)."""
    return round(quote.get("total", 0) / quote["guests"]) if quote.get("guests") else 0


def invoice_from(quote: dict, invoice_id: str, now: str, by: str) -> dict:
    """The draft invoice an order becomes: same customer, lines and rates; it points back to the order."""
    keep = ("customer_id", "customer_name", "lines", "tax_rate", "discount_rate", "subtotal", "discount", "taxable", "tax", "total", "currency")
    event = " ".join(filter(None, [quote.get("event_name"), quote.get("event_date"), quote.get("venue")]))
    return {**{k: quote[k] for k in keep if k in quote}, "invoice_id": invoice_id, "kind": Kind.INVOICE.value, "state": InvoiceState.DRAFT.value,
            "reference": quote.get("order_number", ""), "quote_id": quote["quote_id"], "notes": f"Catering: {event}".strip()[:500],
            "location_id": "", "location_name": "", "created_at": now, "created_by": by, "paid": 0, "credited": 0, "payments": []}
