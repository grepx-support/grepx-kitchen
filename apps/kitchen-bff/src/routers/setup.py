# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Business setup by its owner: business details and modules, locations, items, suppliers, recipes, users and roles,
monthly costs (BUS-02/03/04/06, ACC-01..03, KIT-01/02, ORD-01, COS-01/02)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from grepx_bff.errors import ApiError
from grepx_bff.views import clean
from kitchen import Kitchen, allow, listed

router = APIRouter(prefix="/setup", tags=["setup"])
owner = allow("manage_business")


@router.get("")
def everything(k: Kitchen = Depends(owner)):
    roles = [clean(r) for r in k.gw.rows(gc.access.STAFF_ROLES) if r["_key"].startswith(f"{k.tenant}.")]
    users = []
    for access in k.gw.rows(gc.access.USER_ACCESS):
        person = k.one(gc.people.PEOPLE, access["_key"])
        if person:
            users.append({"id": access["_key"], "name": person.get("name", ""), "email": person.get("email", ""), "phone": person.get("phone", ""),
                          "photo_id": person.get("photo_id", ""),
                          "staff_role_id": access.get("staff_role_id", ""), "perms": access.get("effective") or []})
    return {"business": clean(k.business), "locations": listed([clean(r) for r in k.rows(gc.business.LOCATIONS)], "name"),
            "items": listed([clean(r) for r in k.rows(gc.item.ITEMS)], "kind", "name"),
            "suppliers": listed([clean(r) for r in k.rows(gc.item.SUPPLIERS)], "name"), "recipes": [clean(r) for r in k.rows(gc.item.RECIPES)],
            "roles": roles, "users": sorted(users, key=lambda u: u["name"]), "overheads": [clean(r) for r in k.rows(gc.costing.OVERHEADS)],
            "permissions": [clean(r) for r in k.gw.rows(gc.access.PERMISSION_CATALOG)]}


@router.patch("/business")
def business(body: dict, k: Kitchen = Depends(owner)):
    keep = {f: body[f] for f in ("name", "currency", "timezone", "modules", "settings", "billing") if f in body}
    return k.cmd(gc.business.REQUESTS, gc.business.SERVICE, {"action": "UPDATE", **keep})["business"]


@router.post("/locations")
def location(body: dict, k: Kitchen = Depends(owner)):
    return k.cmd(gc.business.REQUESTS, gc.business.SERVICE, {"action": "SAVE_LOCATION", **body})["location"]


@router.post("/items")
def item(body: dict, k: Kitchen = Depends(owner)):
    return k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_ITEM", **body})["item"]


@router.post("/suppliers")
def supplier(body: dict, k: Kitchen = Depends(owner)):
    return k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_SUPPLIER", **body})["supplier"]


@router.post("/recipes")
def recipe(body: dict, k: Kitchen = Depends(owner)):
    return k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_RECIPE", **body})["recipe"]


ORDERED = {"items": (gc.item.REQUESTS, gc.item.SERVICE, "REORDER"), "suppliers": (gc.item.REQUESTS, gc.item.SERVICE, "REORDER"),
           "locations": (gc.business.REQUESTS, gc.business.SERVICE, "REORDER_LOCATIONS")}


@router.post("/order")
def order(body: dict, k: Kitchen = Depends(owner)):
    """The order items, suppliers or locations are listed in, as the owner dragged them: {list, ids}."""
    target = ORDERED.get(str(body.get("list")))
    if target is None:
        raise ApiError("INVALID_LIST", 400)
    table, service, action = target
    return k.cmd(table, service, {"action": action, "list": body["list"], "ids": list(body.get("ids") or [])})


@router.post("/overheads")
def overhead(body: dict, k: Kitchen = Depends(owner)):
    return k.cmd(gc.costing.REQUESTS, gc.costing.SERVICE, {"action": "SET_OVERHEAD", **body})["overhead"]


class NewUser(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    staff_role: str


def own_role(k: Kitchen, role: str) -> str:
    role_id = role if role.startswith(f"{k.tenant}.") else f"{k.tenant}.{role}"
    if k.gw.one(gc.access.STAFF_ROLES, role_id) is None:
        raise ApiError("UNKNOWN_ROLE", 404)
    return role_id


@router.post("/users")
def add_user(body: NewUser, k: Kitchen = Depends(owner)):
    """ACC-01: the owner creates a user and gives them one role."""
    from grepx_service import Saga, SagaRunner, Step
    from grepx_bff.gateway import CURRENT_TRACE
    if len(body.password) < 8:
        raise ApiError("WEAK_PASSWORD", 400)
    role_id, sealed = own_role(k, body.staff_role), k.gw.box.seal(body.password)
    t = k.tenant
    saga = Saga("business-user", [
        Step("person", gc.people.REQUESTS, gc.people.SERVICE, lambda s: {"action": "CREATE", "tenant_id": t, "name": body.name,
                                                                         "email": body.email, "phone": body.phone, "source": "staff"}),
        Step("login", gc.auth.REQUESTS, gc.auth.SERVICE, lambda s: {"action": "REGISTER", "tenant_id": t, "user_id": s["person"]["person_id"],
                                                                     "email": body.email, "password_enc": sealed}),
        Step("staff", gc.access.REQUESTS, gc.access.SERVICE, lambda s: {"action": "SET_ROLE", "tenant_id": t, "user_id": s["person"]["person_id"],
                                                                         "role": "staff", "actor_id": k.user.user_id}),
        Step("role", gc.access.REQUESTS, gc.access.SERVICE, lambda s: {"action": "SET_STAFF_ROLE", "tenant_id": t,
                                                                        "user_id": s["person"]["person_id"], "staff_role_id": role_id}),
    ])
    outcome = SagaRunner(k.gw.requests).run(saga, {}, trace_id=CURRENT_TRACE.get() or None)
    if not outcome.ok:
        raise ApiError(outcome.reason)
    return {"user_id": outcome.results["person"]["person_id"], "staff_role_id": role_id}


@router.post("/users/{user_id}/role")
def user_role(user_id: str, body: dict, k: Kitchen = Depends(owner)):
    if k.one(gc.people.PEOPLE, user_id) is None:
        raise ApiError("UNKNOWN_PERSON", 404)
    role_id = own_role(k, str(body.get("staff_role") or "")) if body.get("staff_role") else ""
    k.gw.command(gc.access.REQUESTS, gc.access.SERVICE, {"action": "SET_STAFF_ROLE", "tenant_id": k.tenant, "user_id": user_id,
                                                         "staff_role_id": role_id})
    return {"user_id": user_id, "staff_role_id": role_id}


@router.post("/roles/{role}")
def role(role: str, body: dict, k: Kitchen = Depends(owner)):
    """ACC-02/03: what a role of this business may do (e.g. which roles may adjust stock)."""
    role_id = own_role(k, role)
    current = k.gw.one(gc.access.STAFF_ROLES, role_id) or {}
    return k.gw.command(gc.access.REQUESTS, gc.access.SERVICE, {"action": "SAVE_ROLE", "tenant_id": k.tenant, "role_id": role_id,
                                                                "name": body.get("name") or current.get("name", role),
                                                                "description": current.get("description", ""),
                                                                "perms": list(body.get("perms") or [])}).fields
