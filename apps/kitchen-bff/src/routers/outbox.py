# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The business's outbox: every email, WhatsApp and SMS the app sent (or, in test mode, only logged) for it."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from kitchen import Kitchen, allow

router = APIRouter(prefix="/outbox", tags=["outbox"])


@router.get("")
def outbox(k: Kitchen = Depends(allow("manage_business"))):
    rows = sorted(k.rows(gc.notification.NOTIFICATIONS), key=lambda r: r.get("sent_at") or r.get("occurred_at") or "", reverse=True)[:150]
    return {"messages": [{"id": r["_key"], "channel": r.get("channel", ""), "recipient": r.get("recipient", ""), "template": r.get("template", ""),
                          "subject": r.get("subject", ""), "body": r.get("body", ""), "delivery": r.get("delivery", "") or r.get("status", ""),
                          "error": r.get("error", ""), "at": r.get("sent_at") or r.get("occurred_at", "")} for r in rows]}
