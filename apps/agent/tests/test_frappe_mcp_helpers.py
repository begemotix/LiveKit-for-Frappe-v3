"""Phase-05 step 1.2 — tests for the transport-neutral Frappe-MCP helpers.

This module imports only `src.frappe_mcp` (no `agent.py`), so it sidesteps
the pre-existing `JobProcess` pytest-collection issue that affects
`test_mcp_integration.py`. The Type-A byte-for-byte compatibility is still
covered by `test_mcp_integration.py`; here we focus on (a) the dict shape
of the shared helper and (b) the new Type-B client constructor.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest


@pytest.fixture()
def frappe_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FRAPPE_URL", "https://example.test")
    monkeypatch.setenv("FRAPPE_API_KEY", "agent-key")
    monkeypatch.setenv("FRAPPE_API_SECRET", "agent-secret")
    monkeypatch.delenv("FRAPPE_MCP_URL", raising=False)
    monkeypatch.delenv("FRAPPE_MCP_BINARY", raising=False)


# ---------------------------------------------------------------------------
# frappe_mcp_stdio_params
# ---------------------------------------------------------------------------

def test_stdio_params_returns_expected_dict_structure(frappe_env):
    from src.frappe_mcp import frappe_mcp_stdio_params

    params = frappe_mcp_stdio_params()

    assert set(params.keys()) == {"command", "args", "env"}
    assert params["command"] == "npx"
    assert params["args"] == ["-y", "frappe-mcp-server"]
    assert params["env"] == {
        "FRAPPE_URL": "https://example.test",
        "FRAPPE_API_KEY": "agent-key",
        "FRAPPE_API_SECRET": "agent-secret",
    }


def test_stdio_params_respects_custom_binary(frappe_env, monkeypatch):
    monkeypatch.setenv("FRAPPE_MCP_BINARY", "/usr/local/bin/frappe-mcp-server")
    from src.frappe_mcp import frappe_mcp_stdio_params

    params = frappe_mcp_stdio_params()

    # Non-npx binaries get no auto-args — operator must pass a pre-wrapped command.
    assert params["command"] == "/usr/local/bin/frappe-mcp-server"
    assert params["args"] == []


def test_stdio_params_legacy_frappe_mcp_url_derives_origin(monkeypatch):
    monkeypatch.delenv("FRAPPE_URL", raising=False)
    monkeypatch.setenv("FRAPPE_MCP_URL", "https://legacy.example:8443/some/path/mcp")
    monkeypatch.setenv("FRAPPE_API_KEY", "k")
    monkeypatch.setenv("FRAPPE_API_SECRET", "s")
    monkeypatch.delenv("FRAPPE_MCP_BINARY", raising=False)
    from src.frappe_mcp import frappe_mcp_stdio_params

    params = frappe_mcp_stdio_params()

    assert params["env"]["FRAPPE_URL"] == "https://legacy.example:8443"


def test_stdio_params_missing_env_vars_raises(monkeypatch):
    monkeypatch.delenv("FRAPPE_URL", raising=False)
    monkeypatch.delenv("FRAPPE_MCP_URL", raising=False)
    monkeypatch.setenv("FRAPPE_API_KEY", "k")
    monkeypatch.delenv("FRAPPE_API_SECRET", raising=False)
    from src.frappe_mcp import frappe_mcp_stdio_params

    with pytest.raises(ValueError) as exc:
        frappe_mcp_stdio_params()
    msg = str(exc.value)
    assert "Missing required MCP env vars" in msg
    assert "FRAPPE_URL" in msg
    assert "FRAPPE_API_SECRET" in msg


def test_stdio_params_malformed_legacy_url_raises(monkeypatch):
    monkeypatch.delenv("FRAPPE_URL", raising=False)
    monkeypatch.setenv("FRAPPE_MCP_URL", "not-a-url")
    monkeypatch.setenv("FRAPPE_API_KEY", "k")
    monkeypatch.setenv("FRAPPE_API_SECRET", "s")
    from src.frappe_mcp import frappe_mcp_stdio_params

    with pytest.raises(ValueError, match="FRAPPE_MCP_URL must be a valid absolute URL"):
        frappe_mcp_stdio_params()


# ---------------------------------------------------------------------------
# build_frappe_mistral_mcp_client
# ---------------------------------------------------------------------------

def test_build_frappe_mistral_mcp_client_returns_stdio_client(frappe_env):
    from mistralai.extra.mcp.stdio import MCPClientSTDIO
    from mcp import StdioServerParameters
    from src.frappe_mcp import build_frappe_mistral_mcp_client

    client = build_frappe_mistral_mcp_client()

    assert isinstance(client, MCPClientSTDIO)
    # Mistral's client stores its transport config as `_stdio_params`.
    stdio_params = client._stdio_params  # pylint: disable=protected-access
    assert isinstance(stdio_params, StdioServerParameters)
    assert stdio_params.command == "npx"
    assert stdio_params.args == ["-y", "frappe-mcp-server"]
    assert stdio_params.env == {
        "FRAPPE_URL": "https://example.test",
        "FRAPPE_API_KEY": "agent-key",
        "FRAPPE_API_SECRET": "agent-secret",
    }


def test_build_frappe_mistral_mcp_client_propagates_env_error(monkeypatch):
    monkeypatch.delenv("FRAPPE_URL", raising=False)
    monkeypatch.delenv("FRAPPE_MCP_URL", raising=False)
    monkeypatch.delenv("FRAPPE_API_KEY", raising=False)
    monkeypatch.delenv("FRAPPE_API_SECRET", raising=False)
    from src.frappe_mcp import build_frappe_mistral_mcp_client

    with pytest.raises(ValueError, match="Missing required MCP env vars"):
        build_frappe_mistral_mcp_client()


# ---------------------------------------------------------------------------
# build_frappe_mcp_server — smoke-test that Type-A wiring still flows
# through the shared helper (deep assertions remain in test_mcp_integration.py)
# ---------------------------------------------------------------------------

def test_build_frappe_mcp_server_uses_shared_helper(frappe_env):
    class DummyStdio:
        pass

    with patch(
        "livekit.agents.mcp.MCPServerStdio", return_value=DummyStdio()
    ) as mock_stdio:
        from src.frappe_mcp import build_frappe_mcp_server

        server = build_frappe_mcp_server()

    assert isinstance(server, DummyStdio)
    mock_stdio.assert_called_once_with(
        command="npx",
        args=["-y", "frappe-mcp-server"],
        env={
            "FRAPPE_URL": "https://example.test",
            "FRAPPE_API_KEY": "agent-key",
            "FRAPPE_API_SECRET": "agent-secret",
        },
    )


def test_stdio_wiring_log_emitted_with_client_flavor(frappe_env, caplog):
    import logging

    class DummyStdio:
        pass

    with patch("livekit.agents.mcp.MCPServerStdio", return_value=DummyStdio()):
        with caplog.at_level(logging.INFO, logger="src.frappe_mcp"):
            from src.frappe_mcp import build_frappe_mcp_server
            build_frappe_mcp_server()

    flavor_values = [
        getattr(rec, "mcp_client_flavor", None)
        for rec in caplog.records
        if rec.message == "using Frappe MCP via stdio"
    ]
    assert "livekit_mcptoolset" in flavor_values


def test_stdio_wiring_log_emits_mistral_flavor_for_mistral_client(frappe_env, caplog):
    import logging

    with caplog.at_level(logging.INFO, logger="src.frappe_mcp"):
        from src.frappe_mcp import build_frappe_mistral_mcp_client
        build_frappe_mistral_mcp_client()

    flavor_values = [
        getattr(rec, "mcp_client_flavor", None)
        for rec in caplog.records
        if rec.message == "using Frappe MCP via stdio"
    ]
    assert "mistral_mcpclient_stdio" in flavor_values
