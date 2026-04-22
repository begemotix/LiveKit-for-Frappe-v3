import logging
import os
import asyncio
import time
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, llm, Agent, AgentSession
from livekit.agents.llm import mcp
from livekit.agents.voice.turn import TurnHandlingOptions
from livekit.plugins import silero
from src.frappe_mcp import build_frappe_mcp_server, get_allowed_tools_for_mode
from src.mcp_errors import is_permission_error, user_facing_permission_message
from src.mode_config import resolve_agent_mode, validate_mode_env
from src.model_factory import build_voice_pipeline

# Load environment variables
load_dotenv()

def configure_logging():
    logger = logging.getLogger("agent")
    logger.setLevel(logging.INFO)
    
    # Phase 5a Follow-up: Disable propagation to avoid duplicate logs 
    # when running under LiveKit CLI which configures the root logger.
    logger.propagate = False
    
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
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.25,
        min_silence_duration=0.3,
        prefix_padding_duration=0.25,
        activation_threshold=0.5,
        sample_rate=8000,
        force_cpu=True,
    )


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

def _apply_filler_to_toolset(session: AgentSession, toolset: llm.Toolset):
    """
    Phase 2: Wickelt alle Tools eines Toolsets in eine Filler-Logik ein.
    Der Agent spricht eine Filler-Phrase, während das Tool im Hintergrund läuft.
    """
    original_setup = toolset.setup

    async def wrapped_setup(*args, **kwargs):
        await original_setup(*args, **kwargs)
        for tool in toolset.tools:
            # Sicherstellen, dass wir nicht doppelt wrappen
            if hasattr(tool, "_filler_wrapped"):
                continue
                
            # In LiveKit Agents 1.5.x speichern Tools ihre Logik in _func
            if hasattr(tool, "_func"):
                original_func = tool._func
                
                def make_wrapper(fnc):
                    async def wrapped_fnc(*tool_args, **tool_kwargs):
                        # 1. Filler starten (lokal, nicht im Chat-Kontext, unterbrechbar)
                        handle = session.say(
                            "Einen Moment, ich schaue kurz nach.", 
                            allow_interruptions=True,
                            add_to_chat_ctx=False
                        )
                        
                        # 2. Original Tool-Aufruf (parallel zum Filler)
                        result = await fnc(*tool_args, **tool_kwargs)
                        
                        # 3. Filler unterbrechen, sobald das Ergebnis da ist
                        # So wird die Antwort des LLM sofort möglich, ohne auf das Ende des Fillers zu warten.
                        handle.interrupt()
                        
                        return result
                    return wrapped_fnc
                
                tool._func = make_wrapper(original_func)
                tool._filler_wrapped = True
            
        return toolset

    toolset.setup = wrapped_setup


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
    pipeline_metrics = pipeline.get("metrics", {})
    logger.info(
        "pipeline_timing",
        extra={
            "correlation_id": correlation_id,
            "t_pipeline_build_ms": round(float(pipeline_metrics.get("t_pipeline_build_ms", 0.0)), 2),
            "t_ref_audio_read_ms": round(float(pipeline_metrics.get("t_ref_audio_read_ms", 0.0)), 2),
            "t_ref_audio_b64_ms": round(float(pipeline_metrics.get("t_ref_audio_b64_ms", 0.0)), 2),
        },
    )
    tts_observability = pipeline.get("tts_observability", {})
    logger.info(
        "tts_session_config",
        extra={
            "correlation_id": correlation_id,
            "tts_model": tts_observability.get("tts_model"),
            "response_format": tts_observability.get("response_format"),
            "voice_mode": tts_observability.get("voice_mode"),
        },
    )
    effective_agent_name = "voice-eu" if mode == "type_b" else os.getenv("AGENT_NAME", "AI")
    logger.info(
        "resolved_agent_mode",
        extra={"correlation_id": correlation_id, "mode": mode, "agent_name": effective_agent_name},
    )

    # Try to load instructions from Markdown file first (Punkt X - Baseline Training)
    md_instructions = load_agent_instructions()
    
    # Phase 4: Agentisches Prompting für EU-Modus
    pacing_instructions = (
        "WICHTIG für Voice: Antworte IMMER in sehr kurzen, prägnanten Sätzen (max. 12 Wörter). "
        "Mache nach jedem Satz einen Punkt. Vermeide Schachtelsätze oder lange Aufzählungen. "
        "Wenn du ein Tool nutzt, antworte direkt mit den Daten, ohne vorher Füllwörter zu sagen."
    )
    
    agentic_instructions = (
        "\n\nAGENTIC BEHAVIOR (EU-MODE): "
        "1. Merke dir den gesamten Gesprächsverlauf und beziehe dich auf vorherige Aussagen. "
        "2. Antworte kontextuell und vermeide wörtliche Wiederholungen. "
        "3. Nutze natürliche, lebendige Sprache und variiere deine Formulierungen. "
        "4. Wenn der User mehrfach das Gleiche sagt (z.B. 'Hallo'), reagiere jedes Mal anders. "
        "5. Antworte IMMER mit maximal 50 Wörtern. "
        "6. Wenn du Tools nutzt, fasse das Ergebnis kurz und prägnant zusammen."
    )
    
    final_pacing = pacing_instructions + (agentic_instructions if mode == "type_b" else "")
    
    if md_instructions:
        instructions = f"{md_instructions}\n\n{final_pacing}"
    else:
        # Fallback to Environment Variables
        base_instructions = os.getenv("ROLE_DESCRIPTION", "You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.") \
            .replace("{AGENT_NAME}", effective_agent_name) \
            .replace("{COMPANY_NAME}", os.getenv("COMPANY_NAME", "Company"))
        instructions = f"{base_instructions}\n\n{final_pacing}"

    frappe_server = build_frappe_mcp_server()
    # TODO: In Phase 2/3 durch discover_mcp_capabilities(frappe_server) ersetzen.
    # Dieser Aufruf ist aktuell ein TEMPORARY_GUARD für den EU-Modus.
    allowed_tools = get_allowed_tools_for_mode(mode)
    frappe_toolset = mcp.MCPToolset(
        id="frappe_mcp", 
        mcp_server=frappe_server
    )
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
        turn_handling=TurnHandlingOptions(
            turn_detection="vad",
            interruption={
                "mode": "vad",
                "min_duration": 1.2,
                "resume_false_interruption": True,
                "false_interruption_timeout": 2.0,
            },
            preemptive_generation={
                "enabled": True if mode == "type_b" else False,
                "preemptive_tts": True,
                "max_speech_duration": 6.0,
                "max_retries": 3,
            },
        ),
        vad=vad,
        tools=[frappe_toolset],
    )
    
    # Phase 2: Filler-Phase Orchestrierung für EU-Modus
    if mode == "type_b":
        _apply_filler_to_toolset(session, frappe_toolset)
    
    # Phase 5a: Metrik-Instrumentierung
    from src.metrics_listener import MetricsListener
    _metrics_listener = MetricsListener(session, correlation_id, mode=mode)
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
        greeting_flow_started = time.perf_counter()
        greeting_call_started: float | None = None
        t_tts_first_audio_ms: float | None = None
        t_tts_first_chunk_ms: float | None = None
        stt_retry_count: int | None = None

        def _log_session_event(event_name: str):
            def _handler(_ev):
                logger.info(
                    event_name,
                    extra={"correlation_id": correlation_id},
                )
            return _handler

        for event_name in (
            "speech_created",
            "agent_started_speaking",
            "agent_stopped_speaking",
            "agent_speech_interrupted",
            "user_started_speaking",
            "user_input_transcribed",
        ):
            @session.on(event_name)
            def _event_handler(_ev, _event_name=event_name):
                nonlocal t_tts_first_audio_ms, t_tts_first_chunk_ms, stt_retry_count
                if _event_name == "agent_started_speaking":
                    if t_tts_first_audio_ms is None and greeting_call_started is not None:
                        t_tts_first_audio_ms = (time.perf_counter() - greeting_call_started) * 1000
                        t_tts_first_chunk_ms = t_tts_first_audio_ms
                        logger.info(
                            "greeting_tts_first_audio",
                            extra={
                                "correlation_id": correlation_id,
                                "t_tts_first_audio_ms": round(t_tts_first_audio_ms, 2),
                                "t_tts_first_chunk_ms": round(t_tts_first_chunk_ms, 2),
                            },
                        )
                if _event_name == "user_input_transcribed":
                    if isinstance(_ev, dict) and isinstance(_ev.get("retry_count"), int):
                        stt_retry_count = _ev["retry_count"]
                    elif hasattr(_ev, "retry_count"):
                        retry_count_attr = getattr(_ev, "retry_count")
                        if isinstance(retry_count_attr, int):
                            stt_retry_count = retry_count_attr
                _log_session_event(_event_name)(_ev)

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
                "calling session.say for greeting",
                extra={"correlation_id": correlation_id},
            )
            greeting_call_started = time.perf_counter()
            # Begrüßung lokal auslösen (derzeit blockierend gewartet, 
            # könnte in Zukunft als Task entkoppelt werden).
            await session.say("Hallo, wie kann ich helfen?")
            t_session_start_to_greeting_call_ms = (greeting_call_started - greeting_flow_started) * 1000
            t_tts_generate_ms = (time.perf_counter() - greeting_call_started) * 1000
            t_greeting_total_ms = (time.perf_counter() - greeting_flow_started) * 1000
            logger.info(
                "greeting session.say returned",
                extra={
                    "correlation_id": correlation_id,
                    "t_session_start_to_greeting_call_ms": round(t_session_start_to_greeting_call_ms, 2),
                    "t_tts_first_audio_ms": round(t_tts_first_audio_ms, 2) if t_tts_first_audio_ms is not None else None,
                    "t_tts_first_chunk_ms": round(t_tts_first_chunk_ms, 2) if t_tts_first_chunk_ms is not None else None,
                    "t_tts_generate_ms": round(t_tts_generate_ms, 2),
                    "stt_retry_count": stt_retry_count,
                    "t_greeting_total_ms": round(t_greeting_total_ms, 2),
                },
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
