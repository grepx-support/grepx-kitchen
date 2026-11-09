# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""UPDATE - name, currency, time zone (BUS-06), modules on/off (BUS-03), planning and costing settings."""
from grepx_service import RequestContext

from domain import clean_business
from .common import business, guard, save_business


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    current = business(ctx, tenant)
    try:
        row = clean_business({k: ctx.get(k) for k in ("name", "currency", "timezone", "modules", "settings") if ctx.get(k) is not None},
                             current)
    except ValueError as exc:
        return ctx.reject(str(exc))
    ctx.accept({"business": save_business(ctx, tenant, row)})
