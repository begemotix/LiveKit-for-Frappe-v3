from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any
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


def frappe_mcp_stdio_params() -> dict[str, Any]:
    """Resolve stdio-sidecar parameters for the Frappe MCP server.

    Single source of truth for the subprocess contract. Used by
    ``build_frappe_mcp_server()`` which returns a LiveKit
    ``MCPServerStdio`` consumed by both modes via the Phase-2
    pipeline (type_a: ``tools=[MCPToolset(mcp_server=…)]``, type_b:
    ``mcp_servers=[…]``).

    Returns a plain dict with keys ``command``, ``args``, ``env``.

    Raises ``ValueError`` when any of FRAPPE_URL, FRAPPE_API_KEY,
    FRAPPE_API_SECRET is missing, or when the legacy FRAPPE_MCP_URL
    fallback is not a valid absolute URL.
    """
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

    command = os.getenv("FRAPPE_MCP_BINARY", "npx")
    args: list[str] = []
    if command == "npx":
        args = ["-y", "frappe-mcp-server"]

    child_env = {
        "FRAPPE_URL": frappe_url,
        "FRAPPE_API_KEY": api_key,
        "FRAPPE_API_SECRET": api_secret,
    }

    return {
        "command": command,
        "args": args,
        "env": child_env,
    }


def _log_stdio_wiring(params: dict[str, Any], client_flavor: str) -> None:
    safe = _frappe_url_log_fields(params["env"]["FRAPPE_URL"])
    logger.info(
        "using Frappe MCP via stdio",
        extra={
            **safe,
            "mcp_sidecar_command": params["command"],
            "mcp_sidecar_args": list(params["args"]),
            "mcp_effective_transport": "stdio",
            "mcp_binary": params["command"],
            "mcp_client_flavor": client_flavor,
        },
    )


def build_frappe_mcp_server(
    allowed_tools: list[str] | None = None,
) -> mcp.MCPServerStdio:
    """Build a LiveKit ``MCPServerStdio`` for the Frappe MCP subprocess.

    Used by both modes after the Phase-2 standardisation:
    - type_a passes it to ``AgentSession(tools=[MCPToolset(mcp_server=…)])``.
    - type_b passes it to ``AgentSession(mcp_servers=[…])``.

    When ``allowed_tools`` is provided, the returned server's
    ``list_tools()`` is filtered to the allowlist — same semantics as
    LiveKit's upstream ``MCPServerHTTP(allowed_tools=…)``, but for the
    stdio transport which doesn't expose that kwarg natively.
    """
    from livekit.agents import mcp

    params = frappe_mcp_stdio_params()
    _log_stdio_wiring(params, client_flavor="livekit_mcptoolset")

    if not allowed_tools:
        return mcp.MCPServerStdio(
            command=params["command"],
            args=params["args"],
            env=params["env"],
        )

    cls = _get_filtered_mcp_server_stdio_class()
    return cls(
        command=params["command"],
        args=params["args"],
        env=params["env"],
        allowed_tools=allowed_tools,
    )


_filtered_mcp_server_stdio_cache: type | None = None


def _get_filtered_mcp_server_stdio_class() -> type:
    """Lazily build a ``MCPServerStdio`` subclass with a tool-allowlist.

    LiveKit's upstream ``MCPServerStdio`` has no native allowed_tools
    parameter — only ``MCPServerHTTP`` does. This helper produces a
    subclass that mirrors the HTTP transport's filter behaviour, so
    type_b can run on the LiveKit-standard ``mcp_servers=[…]`` path and
    still restrict the Frappe MCP surface to the read-only allowlist
    documented in ``get_allowed_tools_for_mode``.

    Lazy + cached to keep type_a imports cheap; the LiveKit mcp module
    is only imported when the type_b filter path is actually used.
    """
    global _filtered_mcp_server_stdio_cache
    if _filtered_mcp_server_stdio_cache is not None:
        return _filtered_mcp_server_stdio_cache

    from livekit.agents import mcp as _lkmcp
    from livekit.agents.llm.tool_context import (
        get_function_info,
        get_raw_function_info,
        is_function_tool,
        is_raw_function_tool,
    )

    class _FilteredMCPServerStdio(_lkmcp.MCPServerStdio):
        def __init__(
            self,
            *,
            command: str,
            args: list[str],
            env: dict[str, str],
            allowed_tools: list[str],
        ) -> None:
            super().__init__(command=command, args=args, env=env)
            self._allowed_tools_set = set(allowed_tools)

        async def list_tools(self):  # type: ignore[override]
            all_tools = await super().list_tools()
            filtered = []
            for tool in all_tools:
                if is_function_tool(tool):
                    name = get_function_info(tool).name
                elif is_raw_function_tool(tool):
                    name = get_raw_function_info(tool).name
                else:
                    continue
                if name in self._allowed_tools_set:
                    filtered.append(tool)
            return filtered

    _filtered_mcp_server_stdio_cache = _FilteredMCPServerStdio
    return _FilteredMCPServerStdio


def get_allowed_tools_for_mode(mode: str) -> list[str] | None:
    """
    TEMPORARY_GUARD: Manueller Sicherheitsfilter für den EU-Voice-Modus (type_b).

    Diese Funktion wird in einer späteren Phase durch die generische Discovery-Logik
    'discover_mcp_capabilities(server) -> MCPDiscoveryResult' ersetzt, die
    dynamisch über Meta-Tools (z.B. get_frappe_usage_info) den Scope ermittelt.
    """
    if mode == "type_b":
        # Restriktion auf Read-Only Tools zur Reduktion von LLM-Stottern
        # und zur Sicherstellung der Datenresidenz.
        return [
            "get_document",
            "list_documents",
            "get_doctype_schema",
            "get_field_options",
            "find_doctypes",
            "get_module_list",
            "get_frappe_usage_info",
            "get_api_instructions",
            "ping",
            "version"
        ]
    return None

# --- ARCHITEKTUR-VORSCHLAG FÜR PHASE 1c ---
# class MCPDiscoveryResult:
#     allowed_tools: list[str]
#     is_read_only: bool
#     supports_permissions_discovery: bool
#     server_kind: str  # e.g., "frappe"
#
# async def discover_mcp_capabilities(mcp_server, context) -> MCPDiscoveryResult:
#     """
#     Generische Einstiegshöhle für die MCP-Discovery.
#     Wird später in src/mcp/discovery.py ausgelagert.
#     """
#     pass
