# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The business's outbox: every email, WhatsApp and SMS the app sent (or, in test mode, only logged) for it; trying a
failed one again; and which messages go out on which channels, in the business's own words (Outbox -> Settings)."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.errors import ApiError

from kitchen import Kitchen, allow
from views.outbox import messages

router = APIRouter(prefix="/outbox", tags=["outbox"])

# The messages a business sends; "automatic" ones go out by themselves, so on / off and channels apply to them.
OWN = {"stock_alert": True, "payment_reminder": True, "purchase_order": False, "customer_invoice": False}


@router.get("")
def outbox(k: Kitchen = Depends(allow("manage_business"))):
    return {"messages": messages(k.rows(gc.notification.NOTIFICATIONS))}


@router.post("/{key}/retry")
def retry(key: str, k: Kitchen = Depends(allow("manage_business"))):
    return k.cmd(gc.notification.REQUESTS, gc.notification.SERVICE, {"action": "RETRY", "key": key})


@router.get("/settings")
def settings(k: Kitchen = Depends(allow("manage_business"))):
    templates = {t["_key"]: t for t in k.gw.rows(gc.template.MESSAGE_TEMPLATES)}
    out = []
    for key, automatic in OWN.items():
        t = templates.get(key)
        if t is None:
            continue
        mine = k.gw.one(gc.template.MESSAGE_SETTINGS, f"{k.tenant}:{key}")
        mine = mine if mine and mine.get("status") == "ACCEPTED" else None
        out.append({"key": key, "label": t.get("label", key), "automatic": automatic, "placeholders": t.get("placeholders") or [],
                    "default": {"channels": t.get("channels") or [], **{f: (t.get("bodies") or {}).get(f, "") for f in ("subject", "text")}},
                    "mine": mine and {f: mine.get(f) for f in ("enabled", "channels", "subject", "text")}})
    return {"messages": out}


@router.put("/settings/{key}")
def save(key: str, body: dict, k: Kitchen = Depends(allow("manage_business"))):
    if key not in OWN:
        raise ApiError("UNKNOWN_TEMPLATE", 404)
    fields = {"action": "RESET"} if body.get("reset") else {
        "action": "SAVE", "enabled": bool(body.get("enabled", True)), "channels": list(body.get("channels") or []),
        "subject": str(body.get("subject") or ""), "text": str(body.get("text") or "")}
    return k.cmd(gc.template.REQUESTS, gc.template.SERVICE, {**fields, "template_key": key, "for_tenant": k.tenant})
