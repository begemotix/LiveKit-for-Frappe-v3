import os
from unittest.mock import patch

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
