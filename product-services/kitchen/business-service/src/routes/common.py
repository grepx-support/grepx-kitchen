# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reads and writes of this service's own rows."""
from grepx_service import RequestContext

from dto import ReasonCode, Table


def tenant_of(ctx: RequestContext) -> str:
    return ctx.text("tenant_id")


def business(ctx: RequestContext, tenant: str) -> dict | None:
    return ctx.read.accepted_one(Table.BUSINESSES.value, tenant) if tenant else None


def save_business(ctx: RequestContext, tenant: str, row: dict) -> dict:
    full = {"business_id": tenant, "tenant_id": tenant, **row}
    ctx.emitter.submit(Table.BUSINESSES.value, tenant, "ACCEPTED", full)
    return full


def guard(ctx: RequestContext) -> str | None:
    """The tenant of a request for an existing business, or None after rejecting it."""
    tenant = tenant_of(ctx)
    if not tenant:
        ctx.reject(ReasonCode.MISSING_TENANT)
        return None
    if business(ctx, tenant) is None:
        ctx.reject(ReasonCode.UNKNOWN_BUSINESS)
        return None
    return tenant
