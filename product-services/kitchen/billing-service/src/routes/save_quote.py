# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_QUOTE - create or change a quotation (draft or sent; changing a sent one makes it a draft again, revision + 1):
customer, the event (date, time, venue, guests), menu lines with prices, tax and discount rates, notes, valid for N days."""
from grepx_service import RequestContext, new_key, now_iso

from domain import clean_event, clean_lines, may, priced, valid_until
from dto import QuoteState, Table
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(books):
        key = ctx.text("quote_id")
        old = books.quote(key) if key else {}
        if old:
            may("save", old)
        customer = books.customer(ctx.text("customer_id"))
        raw = ctx.get("valid_days")
        valid_until(books.today(), raw)                           # 1 to 365 days (none given: 14), else INVALID_DATE
        days = int(raw) if raw not in (None, "") else 14
        key = key or new_key()
        doc = priced({**{k: v for k, v in old.items() if k in ("number", "sent", "created_at", "created_by")},
                      "quote_id": key, "state": QuoteState.DRAFT.value, "revision": int(old.get("revision") or 0) + (1 if old.get("state") == QuoteState.SENT.value else 0),
                      "customer_id": customer["customer_id"], "customer_name": customer["name"], **clean_event({f: ctx.get(f) for f in
                      ("event_date", "event_time", "venue", "guests", "event_name")}), "lines": clean_lines(ctx.get("lines"), books.items()),
                      "tax_rate": str(ctx.get("tax_rate") or 0), "discount_rate": str(ctx.get("discount_rate") or 0), "notes": ctx.text("notes")[:800],
                      "valid_days": days, "currency": books.business.get("currency", ""),
                      "created_at": old.get("created_at") or now_iso(), "created_by": old.get("created_by") or ctx.text("actor_name")})
        return {"quote": books.save(Table.QUOTES.value, key, doc), "quote_id": key}
    run(ctx, body)
