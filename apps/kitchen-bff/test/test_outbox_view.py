# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from views.outbox import messages


def test_one_line_per_message_with_its_latest_try():
    rows = [{"_key": "a", "action": "SEND", "template": "t", "delivery": "FAILED", "sent_at": "2026-01-01T10:00"},
            {"_key": "a~2", "action": "SEND", "template": "t", "delivery": "SENT", "attempt": 2, "retry_of": "a", "sent_at": "2026-01-01T10:06"},
            {"_key": "b", "action": "SEND", "template": "t", "delivery": "FAILED", "attempt": 4, "sent_at": "2026-01-01T09:00"},
            {"_key": "c", "action": "SEND", "template": "t", "status": "NEW", "occurred_at": "2026-01-01T11:00"},
            {"_key": "r", "action": "RETRY", "key": "b"}]
    got = messages(rows)
    assert [(m["id"], m["delivery"], m["tries"], m["will_retry"]) for m in got] == [
        ("c", "QUEUED", 1, False), ("a~2", "SENT", 2, False), ("b", "FAILED", 4, False)]
    assert messages([{**rows[0]}])[0]["will_retry"] is True
