# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""CREATE - register a business (BUS-01). Its id is the tenant every other row of the business carries."""
from grepx_service import RequestContext

from domain import clean_business
from dto import ReasonCode
from .common import business, save_business, tenant_of


def handle(ctx: RequestContext) -> None:
    tenant = tenant_of(ctx)
    if not tenant:
        return ctx.reject(ReasonCode.MISSING_TENANT)
    if business(ctx, tenant) is not None:
        return ctx.reject(ReasonCode.BUSINESS_EXISTS)
    try:
        row = clean_business(ctx.fields)
    except (ValueError, KeyError) as exc:
        return ctx.reject(str(exc.args[0]) if isinstance(exc, ValueError) else ReasonCode.INVALID_NAME)
    ctx.accept({"business": save_business(ctx, tenant, row)})
