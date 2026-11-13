# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SET_CLOSED - the platform operator closes a business (its people can no longer use the app; nothing is deleted, so it
can be reopened) or reopens it."""
from datetime import datetime, timezone

from grepx_service import RequestContext

from .common import business, guard, save_business


def handle(ctx: RequestContext) -> None:
    tenant = guard(ctx)
    if tenant is None:
        return
    closed = ctx.get("closed") in (True, "true", "1", 1)
    row = {**business(ctx, tenant), "closed": closed,
           "closed_at": datetime.now(timezone.utc).isoformat(timespec="seconds") if closed else "", "closed_by": ctx.text("actor_id") if closed else ""}
    ctx.accept({"business": save_business(ctx, tenant, {k: v for k, v in row.items() if not k.startswith("_")})})
