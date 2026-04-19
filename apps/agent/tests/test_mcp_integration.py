import os
import asyncio
from unittest.mock import patch
from types import SimpleNamespace

import pytest
import agent as agent_module
from src.frappe_mcp import build_frappe_mcp_server


def test_build_frappe_mcp_server_uses_env_headers():
    captured = {}

    class DummyMCPServerHTTP:
        def __init__(self, url, headers):
            captured["url"] = url
            captured["headers"] = headers

    with patch.dict(
        os.environ,
        {
            "FRAPPE_MCP_URL": "https://example.test/mcp",
            "FRAPPE_API_KEY": "agent-key",
            "FRAPPE_API_SECRET": "agent-secret",
        },
        clear=False,
    ):
        with patch("src.frappe_mcp._create_mcp_server", DummyMCPServerHTTP):
            server = build_frappe_mcp_server()

    assert isinstance(server, DummyMCPServerHTTP)
    assert captured["url"] == "https://example.test/mcp"
    assert captured["headers"]["Authorization"] == "token agent-key:agent-secret"


def test_build_frappe_mcp_server_missing_env_raises():
    with patch.dict(
        os.environ,
        {
            "FRAPPE_MCP_URL": "https://example.test/mcp",
            "FRAPPE_API_KEY": "agent-key",
        },
        clear=False,
    ):
        os.environ.pop("FRAPPE_API_SECRET", None)

        try:
            build_frappe_mcp_server()
            assert False, "Expected ValueError for missing FRAPPE_API_SECRET"
        except ValueError as exc:
            assert "Missing required MCP env vars:" in str(exc)
            assert "FRAPPE_API_SECRET" in str(exc)


def test_session_has_mcp_server():
    with open("apps/agent/agent.py", "r", encoding="utf-8") as source_file:
        source = source_file.read()

    assert "mcp_servers=[build_frappe_mcp_server()]" in source


def test_no_runtime_credential_switch():
    with open("apps/agent/agent.py", "r", encoding="utf-8") as source_file:
        source = source_file.read()

    assert "FRAPPE_API_KEY" not in source
    assert "FRAPPE_API_SECRET" not in source
    assert "USER_" not in source
    assert "FRONTEND_" not in source


def test_dynamic_tool_discovery_runtime_evidence():
    with open("apps/agent/agent.py", "r", encoding="utf-8") as source_file:
        source = source_file.read()

    assert "mcp_servers=[build_frappe_mcp_server()]" in source
    assert "allowed_tools" not in source
    assert "tool_allowlist" not in source


def test_no_direct_frappe_api_calls():
    with open("apps/agent/agent.py", "r", encoding="utf-8") as source_file:
        source = source_file.read()

    assert "/api/method" not in source
    assert "requests." not in source
    assert "httpx." not in source
    assert "frappe." not in source


@patch("agent.openai.realtime.RealtimeModel", return_value=object())
@pytest.mark.asyncio
async def test_session_end_cleans_up_mcp_server(_model_patch):
    class FakeMCPServer:
        def __init__(self):
            self.close_calls = 0

        async def aclose(self):
            self.close_calls += 1

    class FakeRoom:
        def __init__(self):
            self.name = "test-room"
            self.remote_participants = {"p1": SimpleNamespace(identity="participant-1")}
            self._handlers = {}

        def on(self, event_name):
            def decorator(func):
                self._handlers[event_name] = func
                return func

            return decorator

    class FakeContext:
        def __init__(self):
            self.room = FakeRoom()
            self.log_context_fields = {}

        async def connect(self):
            return None

    class FakeAgentSession:
        def __init__(self, llm, allow_interruptions, mcp_servers):
            self.llm = llm
            self.allow_interruptions = allow_interruptions
            self.mcp_servers = mcp_servers

        def on(self, _event_name):
            def decorator(func):
                return func

            return decorator

        async def start(self, room, agent):
            self.room = room
            self.agent = agent

        async def generate_reply(self, instructions):
            return instructions

    fake_server = FakeMCPServer()
    created_tasks = []

    def schedule_now(coro):
        task = asyncio.get_running_loop().create_task(coro)
        created_tasks.append(task)
        return task

    with patch("agent.build_frappe_mcp_server", return_value=fake_server), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        ctx = FakeContext()
        await agent_module.entrypoint(ctx)
        disconnect_handler = ctx.room._handlers["participant_disconnected"]
        disconnect_handler(SimpleNamespace(identity="participant-1"))
        await asyncio.gather(*created_tasks)

    assert fake_server.close_calls == 1
