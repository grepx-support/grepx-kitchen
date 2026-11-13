# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The running kitchen site's API, used the way the screens use it (every business rule applies)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class ApiFailed(Exception):
    pass


def site_url() -> str:
    """The site on this machine: SITE_URL's port on localhost (the public address may not route back to itself)."""
    from urllib.parse import urlparse
    port = urlparse(os.environ.get("SITE_URL", "http://localhost:8861")).port or 80
    return f"http://127.0.0.1:{port}"


class Site:
    def __init__(self, base: str | None = None):
        self.base = (base or site_url()).rstrip("/") + "/api/v1"
        self.tokens: dict[str, str] = {}

    def call(self, method: str, path: str, body=None, who: str = ""):
        headers = {"Content-Type": "application/json"}
        if who:
            headers["Authorization"] = f"Bearer {self.tokens[who]}"
        req = urllib.request.Request(self.base + path, method=method, headers=headers,
                                     data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            detail = (json.loads(e.read() or b"{}").get("detail") or {})
            raise ApiFailed(f"{method} {path}: {detail.get('reason') or e.code} {detail.get('message', '')}") from None
        except urllib.error.URLError as e:
            raise ApiFailed(f"the site {self.base} does not answer ({e.reason}) - start it: scripts/run.sh start") from None

    def login(self, who: str, email: str, password: str) -> dict:
        s = self.call("POST", "/auth/login", {"email": email, "password": password})
        self.tokens[who] = s["token"]
        return s

    def get(self, path, who):
        return self.call("GET", path, who=who)

    def post(self, path, body, who):
        return self.call("POST", path, body, who=who)

    def patch(self, path, body, who):
        return self.call("PATCH", path, body, who=who)
