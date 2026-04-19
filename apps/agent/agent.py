import logging
import os
import asyncio
import inspect
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from livekit.agents import JobContext, WorkerOptions, cli, llm, Agent, AgentSession
from livekit.plugins import openai
from src.frappe_mcp import build_frappe_mcp_server

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


async def _cleanup_mcp_server(mcp_server):
    for method_name in ("aclose", "close", "shutdown"):
        method = getattr(mcp_server, method_name, None)
        if method is None:
            continue
        try:
            result = method()
            if inspect.isawaitable(result):
                await result
            return
        except Exception as cleanup_error:
            logger.error(f"MCP cleanup via {method_name} failed: {cleanup_error}")
            return

    logger.warning("MCP cleanup skipped: no supported close method found")

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
    def __init__(self, instructions: str):
        super().__init__(instructions=instructions)

    @llm.function_tool(description="Lookup mock data in the ERP system")
    async def mock_data_lookup(self, query: str):
        logger.info(f"mock_data_lookup called with query: {query}")
        await asyncio.sleep(3)
        return {"status": "success", "data": f"Found info for {query}"}

async def entrypoint(ctx: JobContext):
    # Derive correlation ID from room name (D-10)
    correlation_id = ctx.room.name
    
    # Add correlation context to logging
    ctx.log_context_fields["correlation_id"] = correlation_id
    
    logger.info(
        f"starting agent for room {correlation_id}", 
        extra={"correlation_id": correlation_id}
    )

    # Task 1: Initialize Realtime Model and Server VAD
    filler_instructions = "IMPORTANT: When using a tool, always first say a brief natural filler in the user's language (e.g., 'Einen Moment, ich schaue nach' if German, 'One moment, I'll check that' if English) so the user knows you are working."
    
    # Try to load instructions from Markdown file first (Punkt X - Baseline Training)
    md_instructions = load_agent_instructions()
    
    if md_instructions:
        instructions = f"{md_instructions}\n\n{filler_instructions}"
    else:
        # Fallback to Environment Variables
        base_instructions = os.getenv("ROLE_DESCRIPTION", "You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.") \
            .replace("{AGENT_NAME}", os.getenv("AGENT_NAME", "AI")) \
            .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
        instructions = f"{base_instructions}\n\n{filler_instructions}"

    model = openai.realtime.RealtimeModel(
        modalities=["audio", "text"],
        turn_detection={
            "type": "server_vad",
            "threshold": float(os.getenv("VAD_THRESHOLD", 0.5)),
            "silence_duration_ms": int(os.getenv("VAD_SILENCE_DURATION_MS", 500))
        }
    )

    # Initialize AgentSession
    session = AgentSession(
        llm=model,
        allow_interruptions=True,
        mcp_servers=[build_frappe_mcp_server()],
    )
    frappe_mcp_server = None
    if hasattr(session, "mcp_servers") and session.mcp_servers:
        frappe_mcp_server = session.mcp_servers[0]
    mcp_cleanup_done = False

    @session.on("function_call_start")
    def on_function_call_start(tool_call):
        logger.info(f"starting tool call: {tool_call.name}")

    async def start_agent_session(participant):
        logger.info(f"starting session for participant {participant.identity}")
        
        # Create the agent instance for this session
        agent = Assistant(instructions=instructions)
        
        # Start the session
        await session.start(room=ctx.room, agent=agent)
        
        logger.info(f"session started for {participant.identity}")

        # Task: Initial greeting (via generate_reply to use native speech-to-speech)
        greeting = os.getenv("INITIAL_GREETING", "Hello, I am {AGENT_NAME}. How can I help you today?") \
            .replace("{AGENT_NAME}", os.getenv("AGENT_NAME", "AI")) \
            .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
        await session.generate_reply(instructions=f"Begrüße den Nutzer freundlich mit folgendem Text: {greeting}")

    async def cleanup_session_mcp():
        nonlocal mcp_cleanup_done
        if mcp_cleanup_done:
            return
        mcp_cleanup_done = True
        if frappe_mcp_server is not None:
            await _cleanup_mcp_server(frappe_mcp_server)

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
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, port=port))
