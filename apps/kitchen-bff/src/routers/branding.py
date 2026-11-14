# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The business logo printed on every document (Setup -> Business). The browser sends the picture as a data URL; the
BFF only stages the bytes, media-service makes the PNG (transparency kept) and business-service keeps its id."""
import uuid

import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.routers.photo import decode_picture

from kitchen import Kitchen, allow

router = APIRouter(prefix="/setup", tags=["setup"])
owner = allow("manage_business")


def set_logo(k: Kitchen, logo_id: str) -> dict:
    return k.cmd(gc.business.REQUESTS, gc.business.SERVICE, {"action": "UPDATE", "billing": {"logo_id": logo_id}})["business"]


@router.post("/logo")
def upload_logo(body: dict, k: Kitchen = Depends(owner)):
    k.gw.limit(f"logo:{k.tenant}", rate=10, per=600)
    picture = decode_picture(body.get("image", ""))
    staged = f"staged/{uuid.uuid4().hex}"
    k.gw.storage.put(staged, picture)
    made = k.cmd(gc.media.REQUESTS, gc.media.SERVICE, {"action": gc.media.MediaAction.PROCESS.value, "staged_key": staged,
                                                       "kind": gc.media.MediaKind.LOGO.value, "owner_id": k.tenant})
    logo_id = made.get("media_id") or ""
    return {"logo_id": logo_id, "business": set_logo(k, logo_id)}


@router.delete("/logo")
def remove_logo(k: Kitchen = Depends(owner)):
    return {"logo_id": "", "business": set_logo(k, "")}
