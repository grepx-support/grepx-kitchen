# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The public website: "request a demo" (no login). Kept by lead-service; bots are slowed by a rate limit per address
and turned away by a hidden field."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends, Request

from grepx_bff.security import gateway

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/demo")
def demo(body: dict, request: Request, gw=Depends(gateway)):
    gw.limit(f"lead:{request.client.host if request.client else 'unknown'}", rate=3, per=600)
    fields = {f: body.get(f, "") for f in ("name", "email", "phone", "company", "size", "message", "website")}
    gw.command(gc.lead.REQUESTS, gc.lead.SERVICE, {"action": "SUBMIT", "product": "kitchen", "kind": "demo", **fields})
    return {"ok": True}
