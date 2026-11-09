# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Tenant guard and own-row lookups."""
import grepx_contracts as gc
from grepx_service import RequestContext

from dto import ReasonCode


def guard(ctx: RequestContext) -> str | None:
    tenant = ctx.text("tenant_id")
    if not tenant:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    if ctx.read.accepted_one(gc.business.BUSINESSES, tenant) is None:
        ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
        return None
    return tenant


def mine(ctx: RequestContext, table: str, key: str, tenant: str) -> dict | None:
    """A row of this business, or None (another business's row is treated as not there - BUS-05)."""
    row = ctx.read.accepted_one(table, key) if key else None
    return row if row and row.get("tenant_id") == tenant else None
