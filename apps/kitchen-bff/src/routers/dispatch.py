# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Documents sent with their PDF attached: a purchase order to its supplier, payslips to the team (email carries the
file, WhatsApp gets it as a document). The PDF is made here (routers/pdf.py builders); the owning service decides
whether it may go and to whom, and keeps the record of each send."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.errors import ApiError

from kitchen import Kitchen, allow
from .orders import buyer, purchase
from .pdf import order_file, payslip_file

router = APIRouter(tags=["send"])
owner = allow("manage_business")


@router.post("/orders/{po_id}/send")
def send_order(po_id: str, body: dict, k: Kitchen = Depends(buyer)):
    """Send the order to the supplier (email / WhatsApp / SMS; only logged until the business connects a provider)."""
    files = [order_file(po_id, k).attachment(k.gw.storage)] if body.get("attach", True) else []
    return purchase(k, {"action": "SEND", "po_id": po_id, "channels": body.get("channels") or [],
                                                             "attachments": files})


def send_one(k: Kitchen, month: str, employee_id: str, channels: list[str]) -> dict:
    try:
        file = payslip_file(month, employee_id, k)
        slip = k.cmd(gc.payroll.REQUESTS, gc.payroll.SERVICE, {"action": "SEND_PAYSLIP", "month": month, "employee_id": employee_id,
                                                                "channels": channels, "org": k.business.get("name", ""),
                                                                "attachments": [file.attachment(k.gw.storage)]})["payslip"]
        return {"employee_id": employee_id, "ok": True, "channels": slip["sent"][-1]["channels"]}
    except ApiError as exc:
        return {"employee_id": employee_id, "ok": False, "reason": exc.detail["reason"], "message": exc.detail["message"]}


@router.post("/payroll/payslips/send")
def send_payslips(body: dict, k: Kitchen = Depends(owner)):
    """Send a locked month's payslips: to the people listed (employee_ids), or to everyone on that month's run."""
    month = str(body.get("month") or "")
    names = {s["employee_id"]: s.get("name", "") for s in k.rows(gc.payroll.PAYSLIPS, month=month)}
    ids = body.get("employee_ids") or list(names)
    if not ids:
        raise ApiError("NO_RUN", 409)
    results = [{**send_one(k, month, eid, body.get("channels") or ["email"]), "name": names.get(eid, "")} for eid in dict.fromkeys(ids)]
    return {"sent": sum(r["ok"] for r in results), "results": results}
