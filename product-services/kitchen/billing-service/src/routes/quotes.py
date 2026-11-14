# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""QUOTES - every quotation and order with what a reader sees (expired when past its date), the price per guest, and
the pipeline: how many and how much at each stage, and how many quotes were won."""
from grepx_service import RequestContext

from domain import per_guest, view_status
from .common import run

STAGES = ("draft", "sent", "expired", "ordered", "invoiced", "declined", "cancelled")


def handle(ctx: RequestContext) -> None:
    def body(books):
        today = books.today()
        quotes = sorted(({**q, "status": view_status(q, today), "per_guest": per_guest(q)} for q in books.quotes()),
                        key=lambda q: (q.get("event_date", ""), q.get("created_at", "")), reverse=True)
        stages = {s: {"count": 0, "total": 0} for s in STAGES}
        for q in quotes:
            stages[q["status"]]["count"] += 1
            stages[q["status"]]["total"] += q.get("total", 0)
        decided = sum(stages[s]["count"] for s in ("ordered", "invoiced", "declined"))
        won = stages["ordered"]["count"] + stages["invoiced"]["count"]
        return {"today": today, "quotes": quotes, "stages": stages, "win_rate": round(won * 100 / decided) if decided else None,
                "upcoming": [q for q in reversed(quotes) if q["status"] == "ordered" and q.get("event_date", "") >= today][:10]}
    run(ctx, body)
