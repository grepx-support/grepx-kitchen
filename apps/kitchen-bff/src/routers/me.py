# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The signed-in user's business: details, modules, settings and locations (GET /me itself comes from grepx_bff)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff.security import Principal, current_user, gateway
from grepx_bff.views import clean

router = APIRouter(tags=["me"])


@router.get("/me/business")
def me(user: Principal = Depends(current_user), gw=Depends(gateway)):
    person = gw.one(gc.people.PEOPLE, user.user_id) or {}
    out = {"user_id": user.user_id, "name": person.get("name", ""), "email": person.get("email", ""), "role": user.role,
           "is_staff": user.is_staff, "perms": user.perms, "tenant": user.tenant, "operator": user.is_admin and not user.tenant,
           "support": user.support, "read_only": user.read_only}
    if user.tenant:
        business = gw.one(gc.business.BUSINESSES, user.tenant)
        if business and business.get("tenant_id") == user.tenant:
            out["business"] = clean(business, ("name", "currency", "timezone", "modules", "settings", "billing"))
            out["locations"] = sorted((clean(r) for r in gw.rows(gc.business.LOCATIONS, tenant_id=user.tenant) if r.get("active", True)),
                                      key=lambda r: (r.get("sort") is None, r.get("sort") or 0, not r.get("holding"), r.get("name", "")))
    return out
