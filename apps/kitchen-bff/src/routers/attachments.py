# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Attachments on any record - a supplier's invoice PDF on its bill, a delivery photo, a certificate on a supplier, a
spec sheet on an item. ref names the record ("bill:123"). The browser sends a data URL; media-service checks the type
(documents and pictures only) and keeps the file. Only this business's files are listed or served."""
import base64
import binascii
import re
import uuid

import grepx_contracts as gc
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from grepx_bff.errors import ApiError
from kitchen import Kitchen, allow

router = APIRouter(prefix="/attachments", tags=["attachments"])
anyone = allow()
REF = re.compile(r"^[a-z_]{2,20}:[A-Za-z0-9_.-]{1,64}$")
MAX_BYTES = 10 * 1024 * 1024


def check_ref(ref: str) -> str:
    if not REF.fullmatch(ref or ""):
        raise ApiError("INVALID_REF", 400)
    return ref


def mine(k: Kitchen, media_id: str) -> dict:
    row = k.gw.one(gc.media.MEDIA, media_id)
    if not row or row.get("owner_id") != k.tenant or row.get("kind") != gc.media.MediaKind.FILE.value:
        raise ApiError("NOT_FOUND", 404)
    return row


def shown(row: dict) -> dict:
    return {"id": row["_key"], "name": row.get("name", ""), "ref": row.get("ref", ""), "type": row.get("content_type", ""), "size": row.get("size", 0),
            "note": row.get("note", ""), "by": row.get("by", ""), "at": row.get("at", ""), "url": f"/api/v1/attachments/{row['_key']}/file"}


def decode(data_url: str) -> bytes:
    head, _, body = (data_url or "").partition(",")
    if not head.startswith("data:") or ";base64" not in head:
        raise ApiError("MISSING_FILE", 400)
    if len(body) > MAX_BYTES * 4 // 3 + 4:
        raise ApiError("TOO_LARGE", 413)
    try:
        return base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
        raise ApiError("MISSING_FILE", 400)


@router.get("")
def listing(ref: str = "", k: Kitchen = Depends(anyone)):
    """The files on one record (ref), or every file of the business (no ref), newest first."""
    rows = k.gw.rows(gc.media.MEDIA, owner_id=k.tenant, **({"ref": check_ref(ref)} if ref else {}))
    files = [shown(r) for r in rows if r.get("kind") == gc.media.MediaKind.FILE.value]
    return {"files": sorted(files, key=lambda f: f["at"], reverse=True)}


@router.post("")
def attach(body: dict, k: Kitchen = Depends(anyone)):
    ref = check_ref(body.get("ref", ""))
    k.gw.limit(f"attach:{k.tenant}", rate=60, per=600)
    staged = f"staged/{uuid.uuid4().hex}"
    k.gw.storage.put(staged, decode(body.get("data", "")))
    out = k.cmd(gc.media.REQUESTS, gc.media.SERVICE, {"action": gc.media.MediaAction.ATTACH.value, "staged_key": staged, "owner_id": k.tenant,
                                                      "ref": ref, "name": body.get("name", "file"), "note": body.get("note", ""), "by": k.name})
    return shown({**out, "_key": out["media_id"]})


@router.get("/{media_id}/file")
def file(media_id: str, k: Kitchen = Depends(anyone)):
    row = mine(k, media_id)
    data = k.gw.storage.get(row["key"])
    if data is None:
        raise ApiError("NOT_FOUND", 404)
    name = row.get("name", "file").replace('"', "")
    return Response(data, media_type=row.get("content_type", "application/octet-stream"),
                    headers={"Content-Disposition": f'inline; filename="{name}"', "Cache-Control": "private, max-age=600"})


@router.delete("/{media_id}")
def remove(media_id: str, k: Kitchen = Depends(anyone)):
    mine(k, media_id)
    k.cmd(gc.media.REQUESTS, gc.media.SERVICE, {"action": gc.media.MediaAction.DELETE.value, "media_id": media_id})
    return {"removed": media_id}
