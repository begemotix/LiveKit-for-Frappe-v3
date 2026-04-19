import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from livekit.agents import mcp


def _create_mcp_server(url: str, headers: dict[str, str]):
    from livekit.agents import mcp

    return mcp.MCPServerHTTP(url=url, headers=headers)


def build_frappe_mcp_server() -> "mcp.MCPServerHTTP":
    url = os.getenv("FRAPPE_MCP_URL")
    api_key = os.getenv("FRAPPE_API_KEY")
    api_secret = os.getenv("FRAPPE_API_SECRET")

    missing = []
    if not url:
        missing.append("FRAPPE_MCP_URL")
    if not api_key:
        missing.append("FRAPPE_API_KEY")
    if not api_secret:
        missing.append("FRAPPE_API_SECRET")

    if missing:
        raise ValueError(f"Missing required MCP env vars: {', '.join(missing)}")

    return _create_mcp_server(
        url=url,
        headers={"Authorization": f"token {api_key}:{api_secret}"},
    )
