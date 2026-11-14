# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Round 2: the delivery note - the goods that left, then the driver's and the receiver's signatures once handed over."""
import base64
import io
from datetime import date

from PIL import Image, ImageDraw

from kitchen_stack import env, ok, open_business  # noqa: F401


def signature() -> str:
    img = Image.new("RGBA", (300, 100), (0, 0, 0, 0))
    ImageDraw.Draw(img).line((10, 80, 120, 20, 200, 70, 290, 30), fill=(20, 20, 60, 255), width=4)
    out = io.BytesIO()
    img.save(out, "PNG")
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode()


def test_delivery_note_before_and_after_the_handover(env):
    stack, api = env
    owner = open_business(api, "Note Kitchen", "owner@note.sg")["owner"]
    loc = lambda **b: ok(api.post("/api/v1/setup/locations", headers=owner, json=b))["location_id"]  # noqa: E731
    wh, shop = loc(name="Central store", kind="warehouse"), loc(name="Orchard outlet", kind="store", address="1 Orchard Rd")
    rice = ok(api.post("/api/v1/setup/items", headers=owner, json={"name": "Rice", "kind": "ingredient", "unit": "kg", "cost": 2}))["item_id"]
    ok(api.post("/api/v1/stock/receive", headers=owner, json={"location_id": wh, "lines": [{"item_id": rice, "qty": 50}]}))
    ok(api.post("/api/v1/stock/send", headers=owner, json={"from_location_id": wh, "to_location_id": shop, "lines": [{"item_id": rice, "qty": 12}]}))
    stack.settle()
    trip = ok(api.get("/api/v1/runs", headers=owner))["waiting"][0]["id"]
    before = api.get(f"/api/v1/pdf/delivery/{trip}", headers=owner)
    assert before.status_code == 200 and before.content[:4] == b"%PDF" and b"/Subtype /Image" not in before.content
    assert api.get("/api/v1/pdf/delivery/nope", headers=owner).status_code == 404
    run = ok(api.post("/api/v1/runs", headers=owner, json={"date": date.today().isoformat(), "start_time": "08:00", "name": "Early",
                                                           "vehicle": "Van SBA1234", "delivery_ids": [trip]}))
    ok(api.post(f"/api/v1/runs/{run['run_id']}/start", headers=owner))
    done = ok(api.post(f"/api/v1/runs/{run['run_id']}/stops/{run['stops'][0]['stop_id']}/deliver", headers=owner,
                       json={"receiver": "Mei at Orchard", "signature": signature(), "driver_signature": signature()}))
    assert done["stops"][0]["driver_signature"].startswith("data:image/png")
    stack.settle()
    after = api.get(f"/api/v1/pdf/delivery/{trip}", headers=owner).content
    assert after.count(b"/Subtype /Image") == 2                      # the driver's and the receiver's signatures
    other = open_business(api, "Other Kitchen", "owner@other.sg")["owner"]
    assert api.get(f"/api/v1/pdf/delivery/{trip}", headers=other).status_code == 404       # another business never sees it
