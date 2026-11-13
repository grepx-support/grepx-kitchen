# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The order story view: stage, timeline order and line comparison."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from views import line_view, stage, timeline  # noqa: E402

PO = {"number": "PO-0001", "supplier_name": "Dairy", "created_at": "2026-11-01T09:00", "created_by_name": "Ravi", "state": "received",
      "lines": [{"item_id": "milk", "qty": 10, "item_name": "Milk", "unit": "l"}, {"item_id": "curd", "qty": 4, "item_name": "Curd", "unit": "kg"}],
      "sent": [{"at": "2026-11-01T09:05", "channels": ["email", "whatsapp"], "by": "Aarav"}],
      "received_at": "2026-11-02T08:00", "received_by_name": "Ravi", "received": [{"item_id": "milk", "qty": 9}, {"item_id": "curd", "qty": 4}]}
BILL = {"bill_id": "b1", "supplier_ref": "SUP-1", "entered_at": "2026-11-03T10:00", "entered_by": "Aarav", "total": 12345, "match": "mismatch",
        "approved_by": "Aarav", "approval_note": "short delivery agreed", "state": "paid", "payments": [{"date": "2026-11-04", "amount": 12345, "method": "bank"}]}


def test_stage_follows_the_bills():
    assert stage({"state": "saved"}, []) == "on_order"
    assert stage(PO, []) == "received"
    assert stage(PO, [{**BILL, "state": "approved"}]) == "billed"
    assert stage(PO, [BILL]) == "paid"
    assert stage(PO, [{**BILL, "state": "void"}]) == "received"
    assert stage({"state": "cancelled"}, [BILL]) == "cancelled"


def test_timeline_is_in_time_order_with_every_step():
    events = timeline(PO, [BILL])
    assert [e["kind"] for e in events] == ["made", "sent", "received", "billed", "approved", "paid"]
    assert events[1]["detail"] == "email · whatsapp" and events[2]["detail"] == "1 line(s) differ from the order"
    assert events[3]["detail"] == "total 123.45 · match: mismatch" and events[-1]["title"] == "Paid 123.45"


def test_lines_compare_ordered_and_received():
    rows = line_view(PO, {"milk": {"cost": "2.5"}}, show_cost=True)
    assert (rows[0]["ordered"], rows[0]["received"], rows[0]["difference"], rows[0]["value"]) == (10.0, 9.0, -1.0, 22.5)
    assert rows[1]["difference"] == 0 and rows[1]["value"] == 0
    assert line_view({**PO, "received": None, "state": "saved"}, {})[0]["received"] is None
    assert "value" not in line_view(PO, {})[0]
