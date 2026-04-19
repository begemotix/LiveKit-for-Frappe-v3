from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urlunparse

if TYPE_CHECKING:
    from livekit.agents import mcp

logger = logging.getLogger(__name__)


def _frappe_url_log_fields(frappe_url: str) -> dict[str, object]:
    """Parse Frappe base URL for logging — never log credentials."""
    parsed = urlparse(frappe_url)
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return {
        "frappe_scheme": parsed.scheme,
        "frappe_host": parsed.hostname or "",
        "frappe_port": port,
    }


def _resolve_frappe_base_url() -> str:
    """Prefer FRAPPE_URL (same contract as Cursor); optional legacy FRAPPE_MCP_URL origin."""
    direct = (os.getenv("FRAPPE_URL") or "").strip()
    if direct:
        return direct
    legacy = (os.getenv("FRAPPE_MCP_URL") or "").strip()
    if legacy:
        parsed = urlparse(legacy)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                "FRAPPE_MCP_URL must be a valid absolute URL when used as fallback for FRAPPE_URL"
            )
        origin = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
        logger.warning(
            "frappe_url_legacy_env",
            extra={
                **_frappe_url_log_fields(origin),
                "detail": "FRAPPE_URL unset; using scheme+host from FRAPPE_MCP_URL for stdio sidecar",
            },
        )
        return origin
    return ""


def build_frappe_mcp_server() -> "mcp.MCPServerStdio":
    from livekit.agents import mcp

    frappe_url = _resolve_frappe_base_url()
    api_key = os.getenv("FRAPPE_API_KEY")
    api_secret = os.getenv("FRAPPE_API_SECRET")

    missing: list[str] = []
    if not frappe_url:
        missing.append("FRAPPE_URL")
    if not api_key:
        missing.append("FRAPPE_API_KEY")
    if not api_secret:
        missing.append("FRAPPE_API_SECRET")

    if missing:
        raise ValueError(f"Missing required MCP env vars: {', '.join(missing)}")

    command = "npx"
    args = ["-y", "frappe-mcp-server"]
    child_env = {
        "FRAPPE_URL": frappe_url,
        "FRAPPE_API_KEY": api_key,
        "FRAPPE_API_SECRET": api_secret,
    }

    safe = _frappe_url_log_fields(frappe_url)
    logger.info(
        "using Frappe MCP via stdio",
        extra={
            **safe,
            "mcp_sidecar_command": command,
            "mcp_sidecar_args": list(args),
            "mcp_effective_transport": "stdio",
        },
    )

    return mcp.MCPServerStdio(
        command=command,
        args=args,
        env=child_env,
    )
