# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Pictures the owner adds in Setup: the business logo printed on every document, and each item's picture (item list,
recipe cards, orders). The browser sends a data URL; the BFF only stages the bytes, media-service makes the image
(a logo keeps its clear background as PNG) and the owning service keeps its id."""
import uuid

import grepx_contracts as gc
from fastapi import APIRouter, Depends
from grepx_bff.routers.photo import decode_picture

from kitchen import Kitchen, allow

router = APIRouter(prefix="/setup", tags=["setup"])
owner = allow("manage_business")


def stage(k: Kitchen, data_url: str, kind: str) -> str:
    """The picture processed and stored by media-service; its media id."""
    k.gw.limit(f"picture:{k.tenant}", rate=30, per=600)
    staged = f"staged/{uuid.uuid4().hex}"
    k.gw.storage.put(staged, decode_picture(data_url))
    return k.cmd(gc.media.REQUESTS, gc.media.SERVICE, {"action": gc.media.MediaAction.PROCESS.value, "staged_key": staged,
                                                       "kind": kind, "owner_id": k.tenant}).get("media_id") or ""


def set_logo(k: Kitchen, logo_id: str) -> dict:
    return k.cmd(gc.business.REQUESTS, gc.business.SERVICE, {"action": "UPDATE", "billing": {"logo_id": logo_id}})["business"]


@router.post("/logo")
def upload_logo(body: dict, k: Kitchen = Depends(owner)):
    logo_id = stage(k, body.get("image", ""), gc.media.MediaKind.LOGO.value)
    return {"logo_id": logo_id, "business": set_logo(k, logo_id)}


@router.delete("/logo")
def remove_logo(k: Kitchen = Depends(owner)):
    return {"logo_id": "", "business": set_logo(k, "")}


@router.post("/items/{item_id}/picture")
def item_picture(item_id: str, body: dict, k: Kitchen = Depends(owner)):
    """Add or change an item's picture ({image: data URL}), or remove it ({remove: true})."""
    image = "" if body.get("remove") else stage(k, body.get("image", ""), gc.media.MediaKind.PICTURE.value)
    return k.cmd(gc.item.REQUESTS, gc.item.SERVICE, {"action": "SAVE_ITEM", "item_id": item_id, "image_id": image})["item"]
