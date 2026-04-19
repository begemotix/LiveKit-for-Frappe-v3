import asyncio
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import agent as agent_module
from src.frappe_mcp import build_frappe_mcp_server
from src.mcp_errors import is_permission_error

_AGENT_PY = Path(__file__).resolve().parent.parent / "agent.py"
_ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"


def test_env_example_documents_frappe_stdio_mcp():
    text = _ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "FRAPPE_URL=https://<your-frappe-host>" in text
    assert "stdio" in text.lower()
    assert "FRAPPE_API_KEY=" in text
    assert "FRAPPE_API_SECRET=" in text


def test_mcp_module_import_available():
    try:
        from livekit.agents import mcp  # noqa: F401
    except Exception as exc:  # pragma: no cover - assertion path
        pytest.fail(f"Expected MCP module import to succeed, got: {exc!r}")


def test_agent_module_import_does_not_raise_mcp_import_error():
    try:
        import importlib

        importlib.reload(agent_module)
    except ModuleNotFoundError as exc:
        if "mcp" in str(exc):
            pytest.fail(f"Unexpected MCP import error while importing agent.py: {exc!r}")
        raise


def test_build_frappe_mcp_server_uses_stdio_sidecar():
    class DummyMCPServerStdio:
        pass

    with (
        patch.dict(
            os.environ,
            {
                "FRAPPE_URL": "https://example.test",
                "FRAPPE_API_KEY": "agent-key",
                "FRAPPE_API_SECRET": "agent-secret",
            },
            clear=False,
        ),
        patch(
            "livekit.agents.mcp.MCPServerStdio", return_value=DummyMCPServerStdio()
        ) as mock_stdio,
    ):
        server = build_frappe_mcp_server()

    assert isinstance(server, DummyMCPServerStdio)
    mock_stdio.assert_called_once_with(
        command="npx",
        args=["-y", "frappe-mcp-server"],
        env={
            "FRAPPE_URL": "https://example.test",
            "FRAPPE_API_KEY": "agent-key",
            "FRAPPE_API_SECRET": "agent-secret",
        },
    )


def test_build_frappe_mcp_server_derives_url_from_legacy_frappe_mcp_url():
    class DummyMCPServerStdio:
        pass

    with (
        patch.dict(
            os.environ,
            {
                "FRAPPE_MCP_URL": "https://legacy.example:8443/some/path/mcp",
                "FRAPPE_API_KEY": "k",
                "FRAPPE_API_SECRET": "s",
            },
            clear=False,
        ),
    ):
        os.environ.pop("FRAPPE_URL", None)
        with patch(
            "livekit.agents.mcp.MCPServerStdio", return_value=DummyMCPServerStdio()
        ) as mock_stdio:
            build_frappe_mcp_server()

    mock_stdio.assert_called_once_with(
        command="npx",
        args=["-y", "frappe-mcp-server"],
        env={
            "FRAPPE_URL": "https://legacy.example:8443",
            "FRAPPE_API_KEY": "k",
            "FRAPPE_API_SECRET": "s",
        },
    )


def test_build_frappe_mcp_server_missing_env_raises():
    with patch.dict(
        os.environ,
        {
            "FRAPPE_URL": "https://example.test",
            "FRAPPE_API_KEY": "agent-key",
        },
        clear=False,
    ):
        os.environ.pop("FRAPPE_API_SECRET", None)

        with pytest.raises(ValueError, match="Missing required MCP env vars:") as exc_info:
            build_frappe_mcp_server()
        assert "FRAPPE_API_SECRET" in str(exc_info.value)


def test_session_has_mcp_toolset():
    with open(_AGENT_PY, encoding="utf-8") as source_file:
        source = source_file.read()

    assert "MCPToolset" in source
    assert "tools=[frappe_toolset]" in source
    assert "mcp_servers=" not in source


def test_no_runtime_credential_switch():
    with open(_AGENT_PY, encoding="utf-8") as source_file:
        source = source_file.read()

    assert "FRAPPE_API_KEY" not in source
    assert "FRAPPE_API_SECRET" not in source
    assert "USER_" not in source
    assert "FRONTEND_" not in source


def test_dynamic_tool_discovery_runtime_evidence():
    with open(_AGENT_PY, encoding="utf-8") as source_file:
        source = source_file.read()

    assert "MCPToolset" in source
    assert "tools=[frappe_toolset]" in source
    assert "allowed_tools" not in source
    assert "tool_allowlist" not in source


def test_no_direct_frappe_api_calls():
    with open(_AGENT_PY, encoding="utf-8") as source_file:
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
        def __init__(self, llm, allow_interruptions, tools=None, mcp_servers=None):
            self.llm = llm
            self.allow_interruptions = allow_interruptions
            self.tools = tools or []
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


def test_permission_error_user_friendly_no_retry():
    class FakePermissionError(Exception):
        pass

    err = FakePermissionError("403 permission denied by remote MCP")
    message = agent_module.map_mcp_error_to_user_message(
        err=err,
        correlation_id="cid-403",
        tool_name="frappe_list_documents",
    )

    assert message == "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff."


@pytest.mark.parametrize(
    "text",
    [
        "403 forbidden",
        "permission denied for this resource",
        "Operation not permitted",
        "insufficient permissions to execute tool",
    ],
)
def test_permission_error_marker_detection(text):
    assert is_permission_error(Exception(text)) is True


def test_permission_error_logged_with_correlation(caplog):
    class FakePermissionError(Exception):
        pass

    with caplog.at_level(logging.WARNING, logger="agent"):
        _ = agent_module.map_mcp_error_to_user_message(
            err=FakePermissionError("insufficient permissions"),
            correlation_id="corr-123",
            tool_name="frappe_get_doc",
        )

    matching = [
        record for record in caplog.records
        if record.message == "mcp_permission_denied"
    ]
    assert matching, "Expected mcp_permission_denied warning log"
    assert matching[0].correlation_id == "corr-123"
    assert matching[0].tool == "frappe_get_doc"
