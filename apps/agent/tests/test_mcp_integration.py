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
    """Phase-04 type_a guarantee: no LiveKit-side tool allowlist for type_a.

    Phase-05 type_b no longer shares this guarantee — the Mistral
    RunContext applies the read-only allowlist via
    `tool_configuration={"include": allowed_tools}`. We therefore scope
    the source-level check to the type_a branch of the entrypoint.
    """
    with open(_AGENT_PY, encoding="utf-8") as source_file:
        source = source_file.read()

    # Split on the mode-dispatch boundary; the type_a block sits between
    # `if mode == "type_a":` and the `else:` that introduces type_b.
    type_a_start = source.index('if mode == "type_a":')
    type_a_end = source.index("\n    else:", type_a_start)
    type_a_block = source[type_a_start:type_a_end]

    assert "MCPToolset" in type_a_block
    assert "tools=[frappe_toolset]" in type_a_block
    # No LiveKit-side allowlist is *wired* into the type_a toolset — the
    # MCPToolset instantiation must not carry an `allowed_tools=` kwarg,
    # and there must be no `tool_allowlist` identifier used in that block.
    assert "allowed_tools=" not in type_a_block
    assert "tool_allowlist" not in type_a_block


def test_no_direct_frappe_api_calls():
    with open(_AGENT_PY, encoding="utf-8") as source_file:
        source = source_file.read()

    assert "/api/method" not in source
    assert "requests." not in source
    assert "httpx." not in source
    assert "frappe." not in source


@pytest.mark.asyncio
async def test_session_end_cleans_up_mcp_server():
    """type_a disconnect path: cleanup_session_mcp -> frappe_toolset.aclose().

    Previously this test also patched `agent.openai.realtime.RealtimeModel`,
    but agent.py never imported openai at module scope (the plugin is
    lazily imported inside model_factory.build_voice_pipeline). Post
    Phase-05, the test explicitly forces type_a and patches the pipeline
    factory instead, matching the new mode-aware entrypoint flow.
    """

    class FakeToolset:
        def __init__(self):
            self.id = "frappe_mcp"
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
            self.proc = SimpleNamespace(userdata={"vad": object()})

        async def connect(self):
            return None

    class FakeAgentSession:
        def __init__(self, *args, **kwargs):
            self.tools = kwargs.get("tools") or []
            # MetricsListener introspects these attributes during __init__;
            # keep them present but inert so the fake session is accepted.
            self.llm = kwargs.get("llm")
            self.stt = kwargs.get("stt")
            self.tts = kwargs.get("tts")

        def on(self, _event_name):
            def decorator(func):
                return func

            return decorator

        async def start(self, room, agent):
            self.room = room
            self.agent = agent

        async def say(self, text, **_kwargs):
            return text

    fake_toolset = FakeToolset()
    created_tasks = []

    def schedule_now(coro):
        task = asyncio.get_running_loop().create_task(coro)
        created_tasks.append(task)
        return task

    pipeline = {"llm": object(), "stt": None, "tts": None}

    with patch("agent.resolve_agent_mode", return_value="type_a"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.build_frappe_mcp_server", return_value=object()), \
         patch("agent.mcp.MCPToolset", return_value=fake_toolset), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        ctx = FakeContext()
        await agent_module.entrypoint(ctx)
        disconnect_handler = ctx.room._handlers["participant_disconnected"]
        disconnect_handler(SimpleNamespace(identity="participant-1"))
        await asyncio.gather(*created_tasks)

    assert fake_toolset.close_calls == 1


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


def test_permission_error_logged_with_correlation():
    """agent.py's logger has `propagate = False` so caplog-via-root doesn't
    see the record. We attach a dedicated capture handler to the `agent`
    logger for the duration of the call instead."""

    class FakePermissionError(Exception):
        pass

    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):  # noqa: D401
            captured.append(record)

    handler = _Capture(level=logging.WARNING)
    agent_logger = logging.getLogger("agent")
    agent_logger.addHandler(handler)
    try:
        _ = agent_module.map_mcp_error_to_user_message(
            err=FakePermissionError("insufficient permissions"),
            correlation_id="corr-123",
            tool_name="frappe_get_doc",
        )
    finally:
        agent_logger.removeHandler(handler)

    matching = [rec for rec in captured if rec.message == "mcp_permission_denied"]
    assert matching, "Expected mcp_permission_denied warning log"
    assert matching[0].correlation_id == "corr-123"
    assert matching[0].tool == "frappe_get_doc"
