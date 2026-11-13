# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The scheduler's tick (catalog/schedules.yaml): keep today's and tomorrow's forecast for every business, so the
Forecast page can show how right it was."""
from types import SimpleNamespace

import grepx_contracts as gc
from grepx_service import Emitter, Reader, now_iso

from routes.common import Demand
from routes.snapshot import keep

JOB = "forecast-keep"


def handle_tick(app, row, cfg) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    read, emitter, kept = Reader(app.client), Emitter(app, cfg, cause=row), 0
    for business in read.accepted(gc.business.BUSINESSES):
        if business.get("closed"):
            continue
        kept += len(keep(Demand(SimpleNamespace(read=read, emitter=emitter), business["_key"])))
    emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": kept})
    return kept
