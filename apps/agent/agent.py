import logging
import os
import asyncio
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from livekit.agents import JobContext, WorkerOptions, cli, llm, Agent, AgentSession
from livekit.plugins import openai

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
    )

    @session.on("function_call_start")
    def on_function_call_start(tool_call):
        logger.info(f"starting tool call: {tool_call.name}")

    async def start_agent_session(participant):
        logger.info(f"starting session for participant {participant.identity}")
        
        # Create the agent instance for this session
        agent = Assistant(instructions=instructions)
        
        # Start the session
        await session.start(room=ctx.room, agent=agent)
        
        # Task 2: DSGVO Announcement (mandatory, non-interruptible)
        announcement = os.getenv(
            "MANDATORY_ANNOUNCEMENT",
            "Hinweis: Sie sprechen mit einem KI-Assistenten. Audio-Daten werden zur Verarbeitung an OpenAI in den USA übertragen. Durch Fortsetzen des Gesprächs willigen Sie ein."
        )
        await session.say(announcement, allow_interruptions=False)
        
        # Initial greeting (interruptible)
        greeting = os.getenv("INITIAL_GREETING", "Hello, I am {AGENT_NAME}. How can I help you today?") \
            .replace("{AGENT_NAME}", os.getenv("AGENT_NAME", "AI")) \
            .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
        await session.say(greeting, allow_interruptions=True)

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
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
