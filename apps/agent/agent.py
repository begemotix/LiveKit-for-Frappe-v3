import logging
import os
import asyncio
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, llm, Agent, AgentSession
from livekit.agents.llm import mcp
from livekit.plugins import silero
from src.frappe_mcp import build_frappe_mcp_server
from src.mcp_errors import is_permission_error, user_facing_permission_message
from src.mode_config import resolve_agent_mode, validate_mode_env
from src.model_factory import build_voice_pipeline

# Load environment variables
load_dotenv()

def configure_logging():
    logger = logging.getLogger("agent")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        handler = logging.StreamHandler()
        # Use JSON formatter as per D-09
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = configure_logging()


def map_mcp_error_to_user_message(err: Exception, correlation_id: str, tool_name: str):
    if is_permission_error(err):
        logger.warning(
            "mcp_permission_denied",
            extra={"correlation_id": correlation_id, "tool": tool_name},
        )
        return user_facing_permission_message()
    return None


def load_agent_instructions():
    try:
        # Try to load instructions from MD file (readme/AGENT_PROMPT.md)
        # This works both locally and in Docker when mounted
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "readme", "AGENT_PROMPT.md")
        
        # Also check one level up if not found (for local dev vs docker)
        if not os.path.exists(path):
            path = os.path.join(base_dir, "..", "..", "readme", "AGENT_PROMPT.md")

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                logger.info(f"Loaded agent instructions from {path}")
                return content
    except Exception as e:
        logger.error(f"Error loading instructions from MD: {e}")
    return None

class Assistant(Agent):
    def __init__(self, instructions: str, correlation_id: str):
        super().__init__(instructions=instructions)
        self._correlation_id = correlation_id

    @llm.function_tool(description="Lookup mock data in the ERP system")
    async def mock_data_lookup(self, query: str):
        try:
            logger.info(f"mock_data_lookup called with query: {query}")
            await asyncio.sleep(3)
            return {"status": "success", "data": f"Found info for {query}"}
        except Exception as err:
            user_message = map_mcp_error_to_user_message(
                err=err,
                correlation_id=self._correlation_id,
                tool_name="mock_data_lookup",
            )
            if user_message is not None:
                return {"status": "error", "message": user_message}
            raise


def prewarm_fnc(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


def resolve_num_idle_processes() -> int:
    raw = (os.getenv("AGENT_NUM_IDLE_PROCESSES") or "").strip()
    if not raw:
        return 2
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError("AGENT_NUM_IDLE_PROCESSES must be an integer") from exc
    if parsed < 0:
        raise ValueError("AGENT_NUM_IDLE_PROCESSES must be >= 0")
    return parsed

async def entrypoint(ctx: JobContext):
    # Derive correlation ID from room name (D-10)
    correlation_id = ctx.room.name
    
    # Add correlation context to logging
    ctx.log_context_fields["correlation_id"] = correlation_id
    
    logger.info(
        f"starting agent for room {correlation_id}", 
        extra={"correlation_id": correlation_id}
    )

    mode = resolve_agent_mode()
    validate_mode_env(mode)
    pipeline = build_voice_pipeline(mode)
    effective_agent_name = "voice-eu" if mode == "type_b" else os.getenv("AGENT_NAME", "AI")
    logger.info(
        "resolved_agent_mode",
        extra={"correlation_id": correlation_id, "mode": mode, "agent_name": effective_agent_name},
    )

    filler_instructions = "IMPORTANT: When using a tool, always first say a brief natural filler in the user's language (e.g., 'Einen Moment, ich schaue nach' if German, 'One moment, I'll check that' if English) so the user knows you are working."
    
    # Try to load instructions from Markdown file first (Punkt X - Baseline Training)
    md_instructions = load_agent_instructions()
    
    if md_instructions:
        instructions = f"{md_instructions}\n\n{filler_instructions}"
    else:
        # Fallback to Environment Variables
        base_instructions = os.getenv("ROLE_DESCRIPTION", "You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.") \
            .replace("{AGENT_NAME}", effective_agent_name) \
            .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
        instructions = f"{base_instructions}\n\n{filler_instructions}"

    frappe_server = build_frappe_mcp_server()
    frappe_toolset = mcp.MCPToolset(id="frappe_mcp", mcp_server=frappe_server)
    vad = ctx.proc.userdata.get("vad")
    if vad is None:
        raise RuntimeError(
            "VAD not prewarmed: ctx.proc.userdata['vad'] missing. "
            "Ensure WorkerOptions(prewarm_fnc=prewarm_fnc) is configured."
        )

    session = AgentSession(
        llm=pipeline["llm"],
        stt=pipeline.get("stt"),
        tts=pipeline.get("tts"),
        allow_interruptions=True,
        vad=vad,
        tools=[frappe_toolset],
    )
    mcp_cleanup_done = False
    session_started = False
    session_start_lock = asyncio.Lock()

    @session.on("function_call_start")
    def on_function_call_start(tool_call):
        logger.info(f"starting tool call: {tool_call.name}")

    async def start_agent_session(participant):
        nonlocal session_started
        async with session_start_lock:
            if session_started:
                logger.info(
                    "skip duplicate session start",
                    extra={"correlation_id": correlation_id, "participant": participant.identity},
                )
                return
            session_started = True

        logger.info(f"starting session for participant {participant.identity}")
        try:
            agent = Assistant(instructions=instructions, correlation_id=correlation_id)
            logger.info("agent instance created", extra={"correlation_id": correlation_id})

            await session.start(room=ctx.room, agent=agent)
            logger.info(
                f"session.start() returned for {participant.identity}",
                extra={"correlation_id": correlation_id},
            )

            greeting = os.getenv("INITIAL_GREETING", "Hello, I am {AGENT_NAME}. How can I help you today?") \
                .replace("{AGENT_NAME}", effective_agent_name) \
                .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
            logger.info(
                "calling generate_reply for greeting",
                extra={"correlation_id": correlation_id},
            )
            await session.generate_reply(
                instructions=f"Begrüße den Nutzer freundlich mit folgendem Text: {greeting}"
            )
            logger.info(
                "greeting generate_reply returned",
                extra={"correlation_id": correlation_id},
            )
        except Exception:
            logger.exception(
                "start_agent_session failed",
                extra={"correlation_id": correlation_id},
            )
            raise

    async def cleanup_session_mcp():
        nonlocal mcp_cleanup_done
        if mcp_cleanup_done:
            return
        mcp_cleanup_done = True
        await frappe_toolset.aclose()

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(_participant):
        # Some transports dispatch the disconnect callback before the participant
        # map is fully updated. Treat <=1 as terminal for deterministic cleanup.
        if len(ctx.room.remote_participants) <= 1:
            asyncio.create_task(cleanup_session_mcp())

    @ctx.room.on("participant_joined")
    def on_participant_joined(participant):
        asyncio.create_task(start_agent_session(participant))

    # Core logic will be added in future plans
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()
    logger.info(f"agent connected to room {ctx.room.name}")

    # If participants are already in the room, start session for the first one
    for participant in ctx.room.remote_participants.values():
        asyncio.create_task(start_agent_session(participant))
        break

if __name__ == "__main__":
    port = int(os.getenv("LIVEKIT_AGENT_PORT", 0))
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_fnc,
            num_idle_processes=resolve_num_idle_processes(),
            port=port,
        )
    )
