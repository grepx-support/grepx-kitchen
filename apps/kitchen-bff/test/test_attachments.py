# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Attachments on any record through the kitchen API: attach, list by record and in the library, open, other businesses
can't see it, programs are refused, remove."""
import base64

from kitchen_stack import env, ok, open_business  # noqa: F401

PDF = "data:application/pdf;base64," + base64.b64encode(b"%PDF-1.4 supplier invoice").decode()


def test_attach_list_open_remove(env):
    stack, api = env
    owner = open_business(api, "Files Kitchen", "owner@files.sg")["owner"]
    other = open_business(api, "Other Kitchen", "owner@other.sg")["owner"]
    f = ok(api.post("/api/v1/attachments", headers=owner, json={"ref": "bill:abc", "name": "HM-778.pdf", "data": PDF}))
    assert f["type"] == "application/pdf" and f["name"] == "HM-778.pdf"
    stack.settle()
    assert [x["id"] for x in ok(api.get("/api/v1/attachments?ref=bill:abc", headers=owner))["files"]] == [f["id"]]
    assert ok(api.get("/api/v1/attachments", headers=owner))["files"][0]["ref"] == "bill:abc"
    got = api.get(f"/api/v1/attachments/{f['id']}/file", headers=owner)
    assert got.status_code == 200 and got.content.startswith(b"%PDF")
    assert api.get(f"/api/v1/attachments/{f['id']}/file", headers=other).status_code == 404
    assert ok(api.get("/api/v1/attachments", headers=other))["files"] == []
    exe = "data:application/octet-stream;base64," + base64.b64encode(b"MZ\x90\x00").decode()
    assert api.post("/api/v1/attachments", headers=owner, json={"ref": "bill:abc", "name": "x.exe", "data": exe}).status_code >= 400
    assert api.post("/api/v1/attachments", headers=owner, json={"ref": "<bad>", "name": "a.pdf", "data": PDF}).status_code == 400
    ok(api.delete(f"/api/v1/attachments/{f['id']}", headers=owner))
    stack.settle()
    assert ok(api.get("/api/v1/attachments?ref=bill:abc", headers=owner))["files"] == []
