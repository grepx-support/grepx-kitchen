# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The daily tick (scheduler-service, catalog/schedules.yaml): for every business that turned automatic reminders on,
email the customers whose invoices are 1, 7, 14 or 30 days late - each reminder once."""
from types import SimpleNamespace

import grepx_contracts as gc
from grepx_service import Emitter, Reader, now_iso

from domain import reminder_stage
from reminders import remind
from routes.common import Books

JOB = "billing-reminders"


def handle_tick(app, row, cfg) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    read, emitter, sent = Reader(app.client), Emitter(app, cfg, cause=row), 0
    for business in read.accepted(gc.business.BUSINESSES):
        if not (business.get("billing") or {}).get("auto_reminders"):
            continue
        books = Books(SimpleNamespace(read=read, emitter=emitter), business["_key"])
        today = books.today()
        for inv in books.invoices():
            stage = reminder_stage(inv, today)
            if stage and remind(books, emitter, inv, books.customer(inv["customer_id"]), stage, "automatic"):
                sent += 1
    emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": sent})
    return sent
