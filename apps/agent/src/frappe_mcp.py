from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Callable, Optional
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

    Single source of truth for the subprocess contract. Shared by:
    - Type-A path via `build_frappe_mcp_server()` (LiveKit `MCPServerStdio`).
    - Type-B path via `build_frappe_mistral_mcp_client()` (Mistral `MCPClientSTDIO`).

    Returns a plain dict with keys `command`, `args`, `env`. Both consumers
    accept these as kwargs (LiveKit) or via `StdioServerParameters(**params)`
    (Mistral / modelcontextprotocol), so the helper stays transport-neutral.

    Raises `ValueError` when any of FRAPPE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET
    is missing, or when the legacy FRAPPE_MCP_URL fallback is not a valid
    absolute URL.
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


def build_frappe_mcp_server() -> "mcp.MCPServerStdio":
    """Type-A: build a LiveKit `MCPServerStdio` consumed by `MCPToolset`."""
    from livekit.agents import mcp

    params = frappe_mcp_stdio_params()
    _log_stdio_wiring(params, client_flavor="livekit_mcptoolset")
    return mcp.MCPServerStdio(
        command=params["command"],
        args=params["args"],
        env=params["env"],
    )


class FillerAwareMCPClient:
    """Mistral `MCPClientSTDIO` subclass that fires a callback before
    every tool dispatch. Constructed lazily via
    `_get_filler_aware_mcp_client_class()` so this module stays
    import-cheap for the type_a path that doesn't touch mistralai.

    The callback receives the tool name and is invoked synchronously
    (inside the async `execute_tool` method but before the awaited
    `super().execute_tool(...)`), so it must be cheap and non-blocking
    — typically it just schedules a `session.say(...)` in LiveKit.

    Rationale: type_b hands the tool loop to Mistral's SDK, which
    means LiveKit's own `function_call_start`-style event never fires
    (verified via the 1.5.5 source: no such event exists in
    `livekit/agents/voice/events.py`). The only observable pre-invoke
    point is the MCP client's `execute_tool()` method, which the
    research on 2026-04-23 flagged as the documented extension point
    (`mistralai.extra.mcp.base.MCPClientBase` is a non-final class with
    a public async `execute_tool`). See readme/... for the decision.
    """

    # The real class body is built lazily inside
    # _get_filler_aware_mcp_client_class() so import costs stay in
    # type_b-only code paths. This stub exists so static checkers and
    # documentation tools see something meaningful at module level.


_filler_aware_class_cache: Optional[type] = None


def _get_filler_aware_mcp_client_class() -> type:
    """Lazily build (once) a real MCPClientSTDIO subclass with the
    filler hook. Caches the class so repeated calls are free."""
    global _filler_aware_class_cache
    if _filler_aware_class_cache is not None:
        return _filler_aware_class_cache

    from mistralai.extra.mcp.stdio import MCPClientSTDIO

    class _FillerAwareMCPClient(MCPClientSTDIO):
        def __init__(
            self,
            *args: Any,
            on_tool_execute: Optional[Callable[[str], None]] = None,
            **kwargs: Any,
        ) -> None:
            super().__init__(*args, **kwargs)
            self._on_tool_execute = on_tool_execute

        async def execute_tool(self, name: str, arguments: dict) -> Any:
            # Fire the filler FIRST so the user hears bridging speech
            # while the MCP round-trip (subprocess + Frappe HTTP) runs.
            # Callback must be sync & cheap — LiveKit's session.say()
            # fits that contract.
            if self._on_tool_execute is not None:
                try:
                    self._on_tool_execute(name)
                except Exception:
                    logger.exception(
                        "filler_aware_mcp_callback_failed",
                        extra={"tool_name": name},
                    )
            return await super().execute_tool(name, arguments)

    _filler_aware_class_cache = _FillerAwareMCPClient
    return _FillerAwareMCPClient


def build_frappe_mistral_mcp_client(
    on_tool_execute: Optional[Callable[[str], None]] = None,
) -> Any:
    """Type-B: build a Mistral MCP client consumed by the Mistral RunContext.

    Same stdio sidecar as Type-A (`frappe-mcp-server` via npx, identical
    ENV contract). The returned client is a `FillerAwareMCPClient` (a
    transparent `MCPClientSTDIO` subclass) that fires `on_tool_execute`
    just before each tool dispatch — this is how we bridge Mistral-SDK-
    owned tool calls into LiveKit's `session.say()` filler path, since
    LiveKit never sees these invocations in the type_b architecture.

    Passing `on_tool_execute=None` (the default) preserves exact
    previous behaviour: a plain stdio client with no pre-invoke hook.
    """
    from mcp import StdioServerParameters

    params = frappe_mcp_stdio_params()
    _log_stdio_wiring(params, client_flavor="mistral_mcpclient_stdio")
    cls = _get_filler_aware_mcp_client_class()
    return cls(
        StdioServerParameters(**params),
        on_tool_execute=on_tool_execute,
    )


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
