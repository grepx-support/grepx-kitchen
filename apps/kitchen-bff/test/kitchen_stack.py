# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The kitchen BFF over the kitchen services and the common services it reuses, on an in-memory Nexus - shared by the
end-to-end suites (each test module gets its own stack). New suites: `from kitchen_stack import env, login, ok, open_business`."""
import os
from calendar import monthrange
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from grepx_config import load_config
from grepx_service.catalog import seed_catalog
from grepx_storage import LocalStorage
from grepx_testkit.stack import start_stack

from grepx_bff.gateway import Gateway
from main import create_app

ROOT = Path(__file__).resolve().parents[3]
COMMON = ["common-services/identity", "common-services/people-service", "common-services/notification-service",
          "common-services/template-service", "common-services/task-service", "common-services/audit-log-service",
          "common-services/settings-service", "common-services/scheduler-service", "common-services/lead-service",
          "common-services/media-service", "common-services/employee-service", "common-services/roster-service",
          "common-services/leave-service", "common-services/payroll-service",
          "common-services/compliance-service", "common-services/fund-service"]
MONTH = date.today().isoformat()[:7]


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    uploads = tmp_path_factory.mktemp("media")
    os.environ["UPLOAD_DIR"] = str(uploads)              # the BFF stages pictures where media-service reads them
    stack = start_stack(ROOT, layers=(*COMMON, "product-services/kitchen"))
    assert all(seed_catalog(stack.requests, ROOT / "product-services/kitchen/catalog").values())
    gw = Gateway(stack.client, load_config(ROOT / "apps/kitchen-bff/config"), storage=LocalStorage(uploads))
    api = TestClient(create_app(gw))
    op = stack.call("people_requests", "people-service", {"action": "CREATE", "name": "Gina Operator", "email": "ops@grepx.sg",
                                                           "phone": "+6591234567", "source": "staff"})
    assert op.ok, op.fields
    assert stack.call("auth_requests", "auth-service", {"action": "REGISTER", "user_id": op.fields["person_id"], "email": "ops@grepx.sg",
                                                        "password_enc": gw.box.seal("operator-pw")}).ok
    assert stack.call("access_requests", "access-service", {"action": "SET_ROLE", "user_id": op.fields["person_id"], "role": "admin"}).ok
    return stack, api


def login(api, email, password):
    r = api.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def ok(response):
    assert response.status_code == 200, response.text
    return response.json()




def open_business(api, name: str, email: str, currency: str = "SGD", timezone: str = "Asia/Singapore") -> dict:
    """The operator opens a business; returns its id and the owner's sign-in headers."""
    ops = login(api, "ops@grepx.sg", "operator-pw")
    made = ok(api.post("/api/v1/platform/businesses", headers=ops, json={"name": name, "currency": currency, "timezone": timezone,
              "owner": {"name": f"{name} Owner", "email": email, "phone": "+6590000001", "password": "owner-pass"}}))
    return {"business_id": made["business_id"], "owner": login(api, email, "owner-pass")}
