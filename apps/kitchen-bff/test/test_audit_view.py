# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from views.audit import entries


def test_changes_are_listed_newest_first_and_reads_left_out():
    rows = {"stock": [{"_key": "a", "action": "WASTE", "status": "ACCEPTED", "actor_name": "Meera", "occurred_at": "2026-01-02T10:00",
                       "item_id": "i1", "location_id": "l1", "qty": 3, "note": "burnt", "tenant_id": "t"},
                      {"_key": "b", "action": "ADJUST", "status": "REJECTED", "reason": "NOT_ENOUGH", "occurred_at": "2026-01-02T11:00"},
                      {"_key": "c", "action": "SEND", "status": "NEW", "occurred_at": "2026-01-02T12:00"}],
            "billing": [{"_key": "d", "action": "MONTHLY", "status": "ACCEPTED", "occurred_at": "2026-01-02T13:00"}]}
    got = entries(rows, {"i1": "Paneer", "l1": "Store"})
    assert [(e["id"], e["done"], e["who"]) for e in got] == [("b", False, "the app"), ("a", True, "Meera")]
    assert got[1]["what"] == "Paneer · Store · qty 3 · note burnt" and got[1]["action"] == "Waste" and got[1]["area"] == "Stock"
    assert got[0]["why"] == "NOT_ENOUGH" and "tenant_id" not in got[1]["fields"]
