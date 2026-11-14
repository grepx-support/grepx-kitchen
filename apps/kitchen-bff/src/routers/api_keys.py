# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Setup -> API keys: the owner makes keys for other systems (a website, a POS, a spreadsheet script) - read or write -
sees each key once, and can revoke it. Calls send "X-Api-Key: <key>" to any /api/v1 route; the API is described at
/docs."""
import grepx_contracts as gc
from fastapi import APIRouter, Depends

from grepx_bff import api_keys
from grepx_bff.views import clean
from kitchen import Kitchen, allow

router = APIRouter(prefix="/setup/api-keys", tags=["setup"])
owner = allow("manage_business")


def ask(k: Kitchen, action: str, **fields) -> dict:
    return k.cmd(gc.access.REQUESTS, gc.access.SERVICE, {"action": action, **fields})


@router.get("")
def listing(k: Kitchen = Depends(owner)):
    rows = [{key: v for key, v in clean(r).items() if key != "secret_hash"} for r in k.rows(gc.access.API_KEYS)]
    return {"keys": sorted(rows, key=lambda r: (not r.get("active"), r.get("created_at", "")), reverse=False), "header": "X-Api-Key", "docs": "/docs"}


@router.post("")
def create(body: dict, k: Kitchen = Depends(owner)):
    """A new key - the full key is in this answer only."""
    full, key_id, digest = api_keys.make()
    row = ask(k, gc.access.AccessAction.CREATE_API_KEY.value, key_id=key_id, secret_hash=digest, scope=body.get("scope", "read"), name=body.get("name", ""))
    return {"key": full, "key_id": key_id, "name": row.get("name"), "scope": row.get("scope")}


@router.delete("/{key_id}")
def revoke(key_id: str, k: Kitchen = Depends(owner)):
    ask(k, gc.access.AccessAction.REVOKE_API_KEY.value, key_id=key_id)
    return {"revoked": key_id}
