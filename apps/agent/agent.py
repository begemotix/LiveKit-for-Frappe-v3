import logging
import os
import asyncio
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.plugins import openai
from livekit.agents.voice import AgentSession

# Load environment variables
load_dotenv()

class AssistantFnc(llm.FunctionContext):
    @llm.ai_callable(description="Lookup mock data in the ERP system")
    async def mock_data_lookup(self, query: str):
        logger.info(f"mock_data_lookup called with query: {query}")
        await asyncio.sleep(3)
        return {"status": "success", "data": f"Found info for {query}"}

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
    
    base_instructions = os.getenv("ROLE_DESCRIPTION", "You are a helpful assistant for {COMPANY_NAME}. Your name is {AGENT_NAME}.") \
        .replace("{AGENT_NAME}", os.getenv("AGENT_NAME", "AI")) \
        .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
    
    model = openai.realtime.RealtimeModel(
        instructions=f"{base_instructions}\n\n{filler_instructions}",
        modalities=["audio", "text"],
        turn_detection=openai.realtime.ServerVADOptions(
            threshold=float(os.getenv("VAD_THRESHOLD", 0.5)),
            silence_duration_ms=int(os.getenv("VAD_SILENCE_DURATION_MS", 500))
        ),
        fnc_ctx=AssistantFnc()
    )

    # Initialize AgentSession with allow_interruptions=True and no separate VAD
    session = AgentSession(
        model=model,
        allow_interruptions=True,
    )

    @session.on("function_call_start")
    def on_function_call_start(tool_call):
        logger.info(f"starting tool call: {tool_call.name}")

    async def start_agent_session(participant):
        logger.info(f"starting session for participant {participant.identity}")
        session.start(ctx.room, participant)
        
        # Task 2: DSGVO Announcement (mandatory, non-interruptible)
        announcement = os.getenv("MANDATORY_ANNOUNCEMENT", "Dieser Anruf kann zu Qualitätszwecken aufgezeichnet werden.")
        await session.say(announcement, allow_interruptions=False)
        
        # Initial greeting (interruptible)
        greeting = os.getenv("INITIAL_GREETING", "Hallo! Ich bin {AGENT_NAME} von {COMPANY_NAME}. Wie kann ich Ihnen heute helfen?") \
            .replace("{AGENT_NAME}", os.getenv("AGENT_NAME", "AI")) \
            .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
        await session.say(greeting, allow_interruptions=True)

    @ctx.room.on("participant_joined")
    def on_participant_joined(participant):
        asyncio.create_task(start_agent_session(participant))

    # Core logic will be added in future plans (03-02 and 03-03)
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()
    logger.info(f"agent connected to room {ctx.room.name}")

    # If participants are already in the room, start session for the first one
    for participant in ctx.room.remote_participants.values():
        asyncio.create_task(start_agent_session(participant))
        break

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
