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
    monkeypatch.setenv("GREPX_OLLAMA_URL", "http://127.0.0.1:1")
    plain = ok(api.get("/api/v1/ai/brief", headers=owner))
    assert plain["ai"] is False and "Waste in the last 30 days" in plain["text"]
    stack.settle()
    assert "not running" in ok(api.get(f"/api/v1/ai/jobs/{plain['job_id']}", headers=owner))["why"]
    monkeypatch.setenv("GREPX_AI_FAKE", "1")
    a = ok(api.post("/api/v1/ai/ask", headers=owner, json={"question": "What did we waste most?"}))
    stack.settle()
    assert ok(api.get(f"/api/v1/ai/jobs/{a['job_id']}", headers=owner))["answer"] == "AI: What did we waste most?"
    c = ok(api.post("/api/v1/ai/chat", headers=owner, json={"message": "Which lots expire this week?"}))
    stack.settle()
    assert ok(api.get(f"/api/v1/ai/chats/{c['chat_id']}", headers=owner))["messages"][-1]["content"] == "AI: Which lots expire this week?"
    st = ok(api.get("/api/v1/ai/status", headers=owner))
    assert st["used"] == 2 and st["model"] == "grepx-kitchen"
