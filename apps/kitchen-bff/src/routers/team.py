# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Team: the business's employees across its outlets (employee-service) - profile, outlets, pay basis, documents with
expiry, leaving, clock PIN. Pay is shown only to people who manage the team."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/team", tags=["team"])
manager = allow("manage_people", "manage_business")


def ask(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.employee.REQUESTS, gc.employee.SERVICE, {"action": action, **fields})


@router.get("")
def team(site_id: str = "", k: Kitchen = Depends(manager)):
    return ask(k, "TEAM", site_id=site_id)


@router.post("")
def save(body: dict, k: Kitchen = Depends(manager)):
    return ask(k, "SAVE", **{f: body.get(f) for f in ("employee_id", "name", "email", "phone", "position", "department", "home_site",
                                                         "sites", "start_date", "pay", "user_id", "emergency", "notes")})["employee"]


@router.post("/{employee_id}/documents")
def document(employee_id: str, body: dict, k: Kitchen = Depends(manager)):
    return ask(k, "SET_DOCUMENT", employee_id=employee_id, document=body)["employee"]


@router.delete("/{employee_id}/documents/{doc_id}")
def remove_document(employee_id: str, doc_id: str, k: Kitchen = Depends(manager)):
    return ask(k, "REMOVE_DOCUMENT", employee_id=employee_id, doc_id=doc_id)["employee"]


@router.post("/{employee_id}/end")
def end(employee_id: str, body: dict, k: Kitchen = Depends(manager)):
    return ask(k, "END", employee_id=employee_id, end_date=body.get("end_date"), reason=body.get("reason"))["employee"]


@router.post("/{employee_id}/pin")
def pin(employee_id: str, body: dict, k: Kitchen = Depends(manager)):
    return k.cmd(gc.roster.REQUESTS, gc.roster.SERVICE, {"action": "SET_PIN", "employee_id": employee_id, "pin": str(body.get("pin") or "")})
