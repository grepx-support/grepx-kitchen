# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Platform operator (GrepX staff): set up a new business with its roles and its owner's login (Q2: the team sets up each
business in the MVP; self-service sign-up comes later)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from grepx_service import Saga, SagaRunner, Step, new_key

from grepx_bff.errors import ApiError
from grepx_bff.gateway import CURRENT_TRACE
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
        rows.append({**clean(b, ("name", "currency", "timezone", "modules")), "locations": len(places)})
    return sorted(rows, key=lambda r: r.get("name", ""))


@router.post("/businesses/{tenant_id}/support")
def support(tenant_id: str, body: dict | None = None, user: Principal = Depends(operator), gw=Depends(gateway)):
    """Open a business as platform support: see everything its owner sees, for an hour (read only unless edit: true)."""
    business = gw.one(gc.business.BUSINESSES, tenant_id)
    if business is None:
        raise ApiError("UNKNOWN_BUSINESS", 404)
    return {**open_support(gw, user, tenant_id, edit=bool((body or {}).get("edit"))), "business_name": business.get("name", "")}


@router.get("/leads")
def leads(user: Principal = Depends(operator), gw=Depends(gateway)):
    """Demo requests from the website, newest first."""
    return {"leads": sorted((clean(r) for r in gw.rows(gc.lead.LEADS)), key=lambda r: r.get("created_at", ""), reverse=True)}


@router.post("/leads/{lead_id}")
def follow_up(lead_id: str, body: dict, user: Principal = Depends(operator), gw=Depends(gateway)):
    return gw.command(gc.lead.REQUESTS, gc.lead.SERVICE, {"action": "SET_STATUS", "lead_id": lead_id, "stage": body.get("stage", ""),
                                                           "note": body.get("note", ""), "actor_id": user.user_id}).fields["lead"]


def role_steps(gw, tenant: str) -> list[Step]:
    """A copy of each staff-role template for the new business (ACC-01..03: its owner can then change them)."""
    names = (gw.cfg.get("kitchen") or {}).get("staff_roles") or []
    steps = []
    for name in names:
        template = gw.one(gc.access.STAFF_ROLES, name) or {}
        steps.append(Step(f"role-{name}", gc.access.REQUESTS, gc.access.SERVICE,
                          lambda s, n=name, t=template: {"action": "SAVE_ROLE", "role_id": f"{tenant}.{n}", "name": t.get("name") or n.title(),
                                                         "description": f"{tenant}", "perms": t.get("perms") or [], "tenant_id": tenant}))
    return steps


@router.post("/businesses")
def create_business(body: NewBusiness, user: Principal = Depends(operator), gw=Depends(gateway)):
    if len(body.owner.password) < 8:
        raise ApiError("WEAK_PASSWORD", 400)
    tenant = new_key()[:10]
    owner_role = (gw.cfg.get("kitchen") or {}).get("owner_role") or "owner"
    sealed = gw.box.seal(body.owner.password)
    saga = Saga("business-set-up", [
        Step("business", gc.business.REQUESTS, gc.business.SERVICE,
             lambda s: {"action": "CREATE", "tenant_id": tenant, "name": body.name, "currency": body.currency, "timezone": body.timezone}),
        *role_steps(gw, tenant),
        Step("person", gc.people.REQUESTS, gc.people.SERVICE,
             lambda s: {"action": "CREATE", "tenant_id": tenant, "name": body.owner.name, "email": body.owner.email,
                        "phone": body.owner.phone, "source": "staff", "link": gw.site}),
        Step("login", gc.auth.REQUESTS, gc.auth.SERVICE,
             lambda s: {"action": "REGISTER", "tenant_id": tenant, "user_id": s["person"]["person_id"], "email": body.owner.email,
                        "password_enc": sealed}),
        Step("staff", gc.access.REQUESTS, gc.access.SERVICE,
             lambda s: {"action": "SET_ROLE", "tenant_id": tenant, "user_id": s["person"]["person_id"], "role": "staff",
                        "actor_id": user.user_id}),
        Step("owner", gc.access.REQUESTS, gc.access.SERVICE,
             lambda s: {"action": "SET_STAFF_ROLE", "tenant_id": tenant, "user_id": s["person"]["person_id"],
                        "staff_role_id": f"{tenant}.{owner_role}"}),
    ])
    outcome = SagaRunner(gw.requests).run(saga, {}, trace_id=CURRENT_TRACE.get() or None)
    if not outcome.ok:
        raise ApiError(outcome.reason)
    return {"business_id": tenant, "owner_id": outcome.results["person"]["person_id"]}
