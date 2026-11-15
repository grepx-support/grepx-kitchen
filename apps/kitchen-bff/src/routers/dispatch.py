# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Documents sent with their PDF attached: a purchase order to its supplier (email carries the file, WhatsApp gets it
as a document; payslips go from the shared payroll). The PDF is made here (routers/pdf.py builders); the owning service decides
whether it may go and to whom, and keeps the record of each send."""
from fastapi import APIRouter, Depends

from kitchen import Kitchen
from .orders import buyer, purchase
from .pdf import order_file

router = APIRouter(tags=["send"])


@router.post("/orders/{po_id}/send")
def send_order(po_id: str, body: dict, k: Kitchen = Depends(buyer)):
    """Send the order to the supplier (email / WhatsApp / SMS; only logged until the business connects a provider)."""
    files = [order_file(po_id, k).attachment(k.gw.storage)] if body.get("attach", True) else []
    return purchase(k, {"action": "SEND", "po_id": po_id, "channels": body.get("channels") or [],
                                                             "attachments": files})

