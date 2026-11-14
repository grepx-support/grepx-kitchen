# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The hourly tick (scheduler-service, catalog/schedules.yaml): new alerts for every business, each kept once a day."""
import os

import grepx_contracts as gc
from grepx_service import Emitter, Reader, now_iso

from alerting import check
from routes.common import Stock

JOB = "inventory-alerts"


def handle_tick(app, row, cfg) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    read, emitter, found = Reader(app.client), Emitter(app, cfg, cause=row), 0
    link = os.environ.get("SITE_URL", "").rstrip("/") + "/#/inventory"
    for business in read.accepted(gc.business.BUSINESSES):
        found += len(check(Stock(read, business["_key"]), emitter, link))
    emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": found})
    return found
