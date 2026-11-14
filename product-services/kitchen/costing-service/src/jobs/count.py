# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""stock_requests COUNT accepted -> the cost day of that closing (idempotent: same key, recomputed)."""
from grepx_service import Emitter, Reader

from routes.common import compute_day


def handle_count(app, row, cfg) -> str:
    f = row.fields
    if not f.get("ref") or not f.get("date"):
        return "skipped"              # a count that did not come from a closing (no sales: no COGS)
    done = compute_day(Reader(app.client), Emitter(app, cfg, cause=row), f.get("tenant_id", ""), f.get("location_id", ""), f["date"])
    return "computed" if done else "skipped"
