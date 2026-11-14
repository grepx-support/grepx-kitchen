# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""PRICES - what the business paid each supplier per item over time (optionally one item or one supplier), and the
price rises of the last N days (default 30), jumps first."""
from datetime import date, timedelta

from grepx_service import RequestContext

from domain.prices import points
from .common import run


def handle(ctx: RequestContext) -> None:
    def body(ap):
        item, supplier = ctx.text("item_id"), ctx.text("supplier_id")
        history = [p for p in points(ap.bills()) if (not item or p["item_id"] == item) and (not supplier or p["supplier_id"] == supplier)]
        since = (date.fromisoformat(ap.today()) - timedelta(days=int(ctx.get("days") or 30))).isoformat()
        rises = [{**c, "bill_id": b["bill_id"], "supplier_id": b["supplier_id"], "supplier_name": b.get("supplier_name", ""), "date": b.get("bill_date", "")}
                 for b in ap.bills() if b.get("state") != "void" and b.get("bill_date", "") >= since for c in b.get("price_changes") or [] if c["pct"] > 0]
        return {"points": history, "rises": sorted(rises, key=lambda r: (not r["jump"], -r["pct"])),
                "jump_pct": (ap.business.get("settings") or {}).get("price_jump_pct", 10)}
    run(ctx, body)
