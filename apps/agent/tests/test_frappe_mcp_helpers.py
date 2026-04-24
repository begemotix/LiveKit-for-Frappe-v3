"""Tests for the transport-neutral Frappe-MCP helpers.

This module imports only `src.frappe_mcp` (no `agent.py`), so it sidesteps
the pre-existing `JobProcess` pytest-collection issue that affects
`test_mcp_integration.py`. After the Phase-2 architecture cut-over both
modes flow through `build_frappe_mcp_server()`; the legacy Mistral
`MCPClientSTDIO` factory and its FillerAware wrap are gone, so those
tests have been removed with the code they covered.
"""
from __future__ import annotations

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
# build_frappe_mcp_server — smoke-test that both modes still flow through
# the shared helper (deep assertions remain in test_mcp_integration.py)
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

    with (
        patch("livekit.agents.mcp.MCPServerStdio", return_value=DummyStdio()),
        caplog.at_level(logging.INFO, logger="src.frappe_mcp"),
    ):
        from src.frappe_mcp import build_frappe_mcp_server
        build_frappe_mcp_server()

    flavor_values = [
        getattr(rec, "mcp_client_flavor", None)
        for rec in caplog.records
        if rec.message == "using Frappe MCP via stdio"
    ]
    assert "livekit_mcptoolset" in flavor_values
