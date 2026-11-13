# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""MONTHLY (read only) - this business's figures for each month of a year (default: this year). Nothing is written."""
from grepx_service import RequestContext

from domain import monthly
from .common import run


def year_of(raw, today: str) -> int:
    """The year asked for, or this year when it is missing or not a sensible year."""
    try:
        year = int(raw)
    except (TypeError, ValueError):
        return int(today[:4])
    return year if 2000 <= year <= 2100 else int(today[:4])


def handle(ctx: RequestContext) -> None:
    def body(ap):
        year = year_of(ctx.get("year"), ap.today())
        return {"year": year, "months": monthly(ap.bills(), year)}
    run(ctx, body)
