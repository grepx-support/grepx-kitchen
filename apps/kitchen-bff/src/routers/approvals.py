# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The approvals inbox: everything waiting for a yes or no from this person, in one place - purchase orders above the
owner's amount, supplier bills to approve (mismatches first), leave to decide - and supplier price rises. Each
section shows only to those who may decide it; the decisions themselves are made by the owning services."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow
from .orders import purchase

router = APIRouter(tags=["approvals"])
anyone = allow()
owner = allow("manage_business")
payer = allow("payables", "manage_business")


def orders(k: Kitchen) -> list[dict]:
    return [{"po_id": r["_key"], "number": r.get("number", ""), "supplier_name": r.get("supplier_name", ""), "value": r.get("value", 0),
             "limit": r["approval"].get("limit"), "by": r.get("created_by_name", ""), "at": r.get("updated_at", "")}
            for r in k.rows(gc.purchase.PURCHASE_ORDERS, state="saved") if (r.get("approval") or {}).get("state") == "pending"]


def bills(k: Kitchen) -> list[dict]:
    rows = [{"bill_id": r["_key"], "supplier_name": r.get("supplier_name", ""), "supplier_ref": r.get("supplier_ref", ""), "total": r.get("total", 0),
             "due": r.get("due", ""), "match": r.get("match", ""), "issues": len(r.get("issues") or []),
             "jumps": sum(1 for c in r.get("price_changes") or [] if c.get("jump"))} for r in k.rows(gc.payables.BILLS, state="entered")]
    return sorted(rows, key=lambda b: (b["match"] != "check" and not b["jumps"], b["due"]))


def leave(k: Kitchen) -> list[dict]:
    people = {r["_key"]: r.get("name", "") for r in k.rows(gc.employee.EMPLOYEES)}
    return sorted(({"leave_id": r["_key"], "name": people.get(r.get("employee_id"), ""), "type": r.get("type_name") or r.get("type_id", ""),
                    "first": r.get("first", ""), "last": r.get("last", ""), "days": r.get("days"), "note": r.get("note", "")}
                   for r in k.rows(gc.leave.LEAVES, state="pending")), key=lambda l: l["first"])


def prices(k: Kitchen, **fields) -> dict:
    return k.cmd(gc.payables.REQUESTS, gc.payables.SERVICE, {"action": "PRICES", **fields})


@router.get("/approvals")
def inbox(k: Kitchen = Depends(anyone)):
    can_pay, can_people = k.can("payables") or k.can("manage_business"), k.can("manage_people") or k.can("manage_business")
    out = {"orders": orders(k) if k.can("manage_business") else [], "bills": bills(k) if can_pay else [],
           "leave": leave(k) if can_people else [], "rises": prices(k, days=14)["rises"] if can_pay else []}
    return {**out, "waiting": len(out["orders"]) + len(out["bills"]) + len(out["leave"])}


@router.get("/approvals/prices")
def price_history(item_id: str = "", supplier_id: str = "", days: int = 90, k: Kitchen = Depends(payer)):
    return prices(k, item_id=item_id, supplier_id=supplier_id, days=days)


@router.post("/orders/{po_id}/approve")
def approve_order(po_id: str, body: dict, k: Kitchen = Depends(owner)):
    """The owner's yes, or no with a note, to an order above their approval amount."""
    return purchase(k, {"action": "APPROVE", "po_id": po_id, "approve": bool(body.get("approve")),
                                                             "note": body.get("note", "")})
