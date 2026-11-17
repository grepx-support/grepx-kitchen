# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""AI in the kitchen: the morning brief in plain words when AI is not connected, AI-written when it is; "ask anything"
answered from the kitchen's own numbers and counted against the month's limit."""
from kitchen_stack import env, ok, open_business  # noqa: F401


def test_brief_and_ask(env, monkeypatch):
    stack, api = env
    owner = open_business(api, "Harbour Kitchen", "owner@harbour.sg")["owner"]
    for var in ("GREPX_AI_FAKE", "GREPX_AI_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    plain = ok(api.get("/api/v1/ai/brief", headers=owner))
    assert plain["ai"] is False and "Waste in the last 30 days" in plain["text"] and "not connected" in plain["why"]
    monkeypatch.setenv("GREPX_AI_FAKE", "1")
    a = ok(api.post("/api/v1/ai/ask", headers=owner, json={"question": "What did we waste most?"}))
    assert a["ai"] and a["answer"] == "AI: What did we waste most?"
    assert ok(api.get("/api/v1/ai/status", headers=owner))["used"] == 1
    assert ok(api.get("/api/v1/ai/brief", headers=owner))["ai"] is True
