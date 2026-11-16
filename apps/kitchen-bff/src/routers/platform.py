# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Platform operator (GrepX staff): set up a new business with its roles and its owner's login (Q2: the team sets up each
business in the MVP; self-service sign-up comes later)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from grepx_bff.errors import ApiError
from grepx_bff.onboarding import open_business
from grepx_bff.security import Principal, admin, gateway
from grepx_bff.support import open_support
from grepx_bff.views import clean

router = APIRouter(prefix="/platform", tags=["platform"])


class Owner(BaseModel):
    name: str
    email: str
    phone: str
    password: str


class NewBusiness(BaseModel):
    name: str
    currency: str
    timezone: str
    owner: Owner


def operator(user: Principal = Depends(admin)) -> Principal:
    if user.tenant:
        raise ApiError("FORBIDDEN", 403)
    return user


@router.get("/businesses")
def businesses(user: Principal = Depends(operator), gw=Depends(gateway)):
    rows = []
    for b in gw.rows(gc.business.BUSINESSES):
        places = gw.rows(gc.business.LOCATIONS, tenant_id=b["_key"])
        rows.append({**clean(b, ("name", "currency", "timezone", "modules", "closed", "closed_at")), "locations": len(places)})
    return sorted(rows, key=lambda r: r.get("name", ""))


@router.post("/businesses/{tenant_id}/support")
def support(tenant_id: str, body: dict | None = None, user: Principal = Depends(operator), gw=Depends(gateway)):
    """Open a business as platform support: see everything its owner sees, for an hour (read only unless edit: true)."""
    business = gw.one(gc.business.BUSINESSES, tenant_id)
    if business is None:
        raise ApiError("UNKNOWN_BUSINESS", 404)
    return {**open_support(gw, user, tenant_id, edit=bool((body or {}).get("edit"))), "business_name": business.get("name", "")}


@router.post("/businesses/{tenant_id}/{verb}")
def close_or_reopen(tenant_id: str, verb: str, user: Principal = Depends(operator), gw=Depends(gateway)):
    """Close a business (its people can no longer use the app; nothing is deleted) or reopen it."""
    if verb not in ("close", "reopen"):
        raise ApiError("NOT_FOUND", 404)
    if gw.one(gc.business.BUSINESSES, tenant_id) is None:
        raise ApiError("UNKNOWN_BUSINESS", 404)
    out = gw.command(gc.business.REQUESTS, gc.business.SERVICE, {"action": gc.business.BusinessAction.SET_CLOSED.value, "tenant_id": tenant_id,
                                                                 "closed": verb == "close", "actor_id": user.user_id})
    return {"business_id": tenant_id, "closed": out.fields["business"]["closed"]}


@router.get("/leads")
def leads(user: Principal = Depends(operator), gw=Depends(gateway)):
    """Demo requests from the website, newest first."""
    return {"leads": sorted((clean(r) for r in gw.rows(gc.lead.LEADS)), key=lambda r: r.get("created_at", ""), reverse=True)}


@router.post("/leads/{lead_id}")
def follow_up(lead_id: str, body: dict, user: Principal = Depends(operator), gw=Depends(gateway)):
    return gw.command(gc.lead.REQUESTS, gc.lead.SERVICE, {"action": "SET_STATUS", "lead_id": lead_id, "stage": body.get("stage", ""),
                                                           "note": body.get("note", ""), "actor_id": user.user_id}).fields["lead"]


@router.post("/businesses")
def create_business(body: NewBusiness, user: Principal = Depends(operator), gw=Depends(gateway)):
    """The platform operator sets up a business (the same set-up as a self-service sign-up: grepx_bff.onboarding)."""
    if len(body.owner.password) < 8:
        raise ApiError("WEAK_PASSWORD", 400)
    return open_business(gw, section="kitchen", name=body.name, currency=body.currency, timezone=body.timezone,
                         owner=body.owner.model_dump(exclude={"password"}), password_enc=gw.box.seal(body.owner.password), actor_id=user.user_id)
