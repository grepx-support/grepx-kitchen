# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The Outbox's rows: one line per message, showing its latest try (failed sends are tried again as new rows)."""

TRIES = 4                                      # notification-service: the first try and three more


def at(row: dict) -> str:
    return row.get("sent_at") or row.get("occurred_at") or ""


def messages(rows: list[dict], limit: int = 300) -> list[dict]:
    latest: dict[str, dict] = {}
    for r in rows:
        if r.get("action", "SEND") != "SEND" or not r.get("template"):
            continue
        first = r.get("retry_of") or r["_key"]
        if int(r.get("attempt") or 1) >= int((latest.get(first) or {}).get("attempt") or 0):
            latest[first] = r
    out = [line(r) for r in latest.values()]
    return sorted(out, key=lambda m: m["at"], reverse=True)[:limit]


def line(r: dict) -> dict:
    delivery = r.get("delivery", "") or ("QUEUED" if r.get("status") in ("NEW", "CLAIMED") else r.get("status", ""))
    tries = int(r.get("attempt") or 1)
    return {"id": r["_key"], "channel": r.get("channel", ""), "recipient": r.get("recipient", ""), "template": r.get("template", ""),
            "subject": r.get("subject", ""), "body": r.get("body", ""), "delivery": delivery, "error": r.get("error", ""),
            "at": at(r), "tries": tries, "will_retry": delivery == "FAILED" and tries < TRIES}
