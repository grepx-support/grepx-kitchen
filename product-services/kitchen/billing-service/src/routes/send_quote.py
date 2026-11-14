# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SEND_QUOTE - give the quote its number the first time (Q-2026-0001), date it today with its valid-until date, and
email it to the customer with the PDF the caller made attached (attachments=[{name, mime, data_b64, url}]).
Without send = true it is only marked as sent (handed over in person). number_only = true only numbers and dates it
(so the PDF made for the email shows them) and leaves it a draft."""
from grepx_service import RequestContext, notify, now_iso

from domain import may, numbered, valid_until
from dto import QuoteState, ReasonCode, Table
from .common import Stop, run


def handle(ctx: RequestContext) -> None:
    def body(books):
        q = books.quote(ctx.text("quote_id"))
        may("send", q)
        today = books.today()
        number = q.get("number") or numbered("Q", int(today[:4]), [x.get("number", "") for x in books.quotes()])
        q = {**q, "number": number, "quoted_on": today, "valid_until": valid_until(today, q.get("valid_days"))}
        if ctx.get("number_only"):
            return {"quote": books.save(Table.QUOTES.value, q["quote_id"], q)}
        q = {**q, "state": QuoteState.SENT.value, "sent": [*(q.get("sent") or []), {"at": now_iso(), "by": ctx.text("actor_name"), "emailed": bool(ctx.get("send"))}]}
        if ctx.get("send"):
            customer = books.customer(q["customer_id"])
            biz = books.business
            if not notify(ctx.emitter, "catering_quote", email=customer.get("email", ""), channels=["email"], auto=False, tenant_id=books.tenant,
                          ref=f"quote-{q['quote_id']}-{len(q['sent'])}", attachments=[a for a in ctx.get("attachments") or [] if isinstance(a, dict)] or None,
                          values={"org": biz.get("name", ""), "customer": customer.get("name", ""), "number": number, "valid_until": q["valid_until"],
                                  "total": f"{biz.get('currency', '')} {q['total'] / 100:,.2f}", "event": q.get("event_date", "")}):
                raise Stop(ReasonCode.NO_EMAIL)
        return {"quote": books.save(Table.QUOTES.value, q["quote_id"], q)}
    run(ctx, body)
