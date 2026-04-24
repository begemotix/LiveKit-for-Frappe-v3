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
from src.audio_buffer_patch import apply_audio_buffer_patch
from src.frappe_mcp import build_frappe_mcp_server, get_allowed_tools_for_mode
from src.mcp_errors import is_permission_error, user_facing_permission_message
from src.mistral_agent import MistralDrivenAgent
from src.mistral_orchestrator import MistralOrchestrator
from src.mode_config import resolve_agent_mode, resolve_mistral_config, validate_mode_env
from src.model_factory import build_voice_pipeline
from src.tts_text_transforms import NumberTransform, PronunciationTransform

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


def _resolve_effective_agent_name(mode: str) -> str:
    """Mirror the entrypoint's effective_agent_name logic so the prewarm
    phase can build the exact same greeting text that the session will
    later request. If the two diverge, cache lookup will miss."""
    return "voice-eu" if mode == "type_b" else os.getenv("AGENT_NAME", "AI")


def _build_greeting_text(mode: str) -> str:
    """Resolve INITIAL_GREETING with the same placeholder substitutions
    the entrypoint applies. Used at prewarm time to pre-synthesize, and
    at session start time to look up the cache."""
    agent_name = _resolve_effective_agent_name(mode)
    company = os.getenv("COMPANY_NAME", "Company")
    default_greeting = "Hello, I am {AGENT_NAME}. How can I help you today?"
    return (
        os.getenv("INITIAL_GREETING", default_greeting)
        .replace("{AGENT_NAME}", agent_name)
        .replace("{COMPANY_NAME}", company)
    )


async def _collect_greeting_frames_async(tts, text: str) -> list:
    """Drive the TTS synthesize() stream to completion and return the
    collected AudioFrame list. The StreamAdapter-wrapped Voxtral TTS
    yields SynthesizedAudio items, each with a .frame attribute."""
    frames: list = []
    async with tts.synthesize(text) as stream:
        async for synthesized_audio in stream:
            frame = getattr(synthesized_audio, "frame", None)
            if frame is not None:
                frames.append(frame)
    return frames


def _prewarm_greeting_audio(proc: JobProcess, mode: str) -> None:
    """Pre-synthesize the greeting once per worker and cache the audio
    frames in proc.userdata. Best-effort: any exception during this
    step is logged and swallowed — start_agent_session falls back to
    live synthesis, so a failed prewarm is not fatal for the worker.

    Prewarm is defined as a *sync* callable by LiveKit Agents; we use
    asyncio.run() to drive the async TTS synthesize() generator from
    this sync context. No running loop exists at prewarm time, so
    asyncio.run() is safe here and fails loudly if misused elsewhere.
    """
    try:
        text = _build_greeting_text(mode)
        pipeline = build_voice_pipeline(mode)
        tts = pipeline.get("tts")
        if tts is None:
            # type_a uses OpenAI Realtime which doesn't expose a TTS
            # instance — there's nothing to pre-synthesize on that path.
            logger.info(
                "greeting_prewarm_skipped_no_tts", extra={"mode": mode}
            )
            return
        frames = asyncio.run(_collect_greeting_frames_async(tts, text))
        if not frames:
            logger.warning(
                "greeting_prewarm_empty_frames",
                extra={"mode": mode, "text_length": len(text)},
            )
            return
        proc.userdata["greeting_audio"] = frames
        proc.userdata["greeting_audio_key"] = text
        logger.info(
            "greeting_prewarm_cached",
            extra={
                "mode": mode,
                "frame_count": len(frames),
                "text_length": len(text),
            },
        )
    except Exception:
        # Never fail the worker over greeting caching — live fallback
        # exists in start_agent_session.
        logger.exception("greeting_prewarm_skipped")


def prewarm_fnc(proc: JobProcess) -> None:
    # Silero VAD settings — tuned for production voice agents.
    # sample_rate=16000 is the LiveKit Silero default and matches the
    # STT plugin's internal SAMPLE_RATE=16000. Earlier we set 8000
    # (telephony quality) which forced resampling in the pipeline and
    # caused the classic "inference is slower than realtime" backlog
    # when multiple Cloud calls (Voxtral STT/TTS + Mistral) ran in
    # parallel — visible in production logs as a 0.4-1.4s VAD delay
    # and audible to the user as a stuttering reply cadence.
    # force_cpu is left unset so LiveKit picks GPU if available and
    # falls back to CPU otherwise; forcing CPU was a preliminary
    # safety that doesn't match what LiveKit's own quick-start ships.
    # Phase 1 / Commit 3: min_silence_duration auf 0.25 s justiert.
    # Vorher war 0.2 s (Humanisierung Tier 1) an der Untergrenze für
    # Silero — im realen Frontend-Test schnitt es vereinzelt User-
    # Satzenden ab. 0.25 s ist der Kompromiss: kürzer als der LiveKit-
    # Default (0.3 s), aber sicherer Puffer gegen halbe Sekundenpausen
    # mitten im Satz. Bei weiteren Abschnitten wieder in Richtung 0.3
    # erhöhen.
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.25,
        min_silence_duration=0.25,
        prefix_padding_duration=0.25,
        activation_threshold=0.5,
        sample_rate=16000,
    )

    # Phase 1 / Commit 1: pre-synthesize the greeting once so
    # session.say can play it from cache instead of triggering a live
    # Voxtral-TTS roundtrip on every call. See session.say(audio=...)
    # docs at https://docs.livekit.io/agents/multimodality/audio/.
    try:
        mode = resolve_agent_mode()
        validate_mode_env(mode)
        _prewarm_greeting_audio(proc, mode)
    except Exception:
        # ENV validation / mode resolution failures here are logged but
        # non-fatal: the entrypoint will re-raise them with full context
        # when it runs.
        logger.exception("greeting_prewarm_outer_failure")


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

    Phase-05 refactor: historically wired for type_b (EU voice path) before
    the Mistral RunContext owned the tool loop. type_b no longer uses
    LiveKit MCPToolsets at all (D-16), so the current code has **no call
    site**. The helper is kept as a dormant option for type_a if an
    operator later decides to add filler to the US path.
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
                        
                        # 3. Filler unterbrechen, sobald das Ergebnis da ist (nur wenn er noch läuft)
                        # So wird die Antwort des LLM sofort möglich, ohne auf das Ende des Fillers zu warten.
                        if not handle.done():
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

    # Experiment A: raise WebRTC jitter buffer from Agents' hardcoded
    # 200 ms to 500 ms so gaps between Voxtral sentence-batch HTTP
    # round-trips are partially absorbed. Idempotent per-process.
    apply_audio_buffer_patch(queue_size_ms=500)

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

    vad = ctx.proc.userdata.get("vad")
    if vad is None:
        raise RuntimeError(
            "VAD not prewarmed: ctx.proc.userdata['vad'] missing. "
            "Ensure WorkerOptions(prewarm_fnc=prewarm_fnc) is configured."
        )

    allowed_tools = get_allowed_tools_for_mode(mode)

    # Phase 1 / Commit 2: LLM output is normalised through these
    # transforms before it reaches the TTS plugin. NumberTransform
    # rewrites HH:MM times so Voxtral doesn't pronounce the colon;
    # PronunciationTransform fixes proper-name pronunciation that
    # Voxtral reliably gets wrong ("Frappe" as English).
    # Both are lightweight callable instances — constructed once per
    # session, shared internally across all TTS chunks. The list order
    # matters: numbers first, then pronunciation fix-ups.
    tts_transforms = [
        NumberTransform(),
        PronunciationTransform({"Frappe": "Frapp"}),
    ]

    # Mode-specific session wiring. type_a keeps the original LiveKit
    # MCPToolset path; type_b hands the entire tool loop to the Mistral
    # SDK via MistralOrchestrator and feeds plain text into LiveKit TTS
    # through MistralDrivenAgent.llm_node (Phase-05 D-16, D-17).
    frappe_toolset: llm.Toolset | None = None
    orchestrator: MistralOrchestrator | None = None

    if mode == "type_a":
        frappe_server = build_frappe_mcp_server()
        # TEMPORARY_GUARD — see frappe_mcp.get_allowed_tools_for_mode;
        # the LiveKit MCPToolset consumes the full inventory and we
        # rely on Frappe's per-user permissions for read-only guardrails.
        frappe_toolset = mcp.MCPToolset(
            id="frappe_mcp",
            mcp_server=frappe_server,
        )
        session = AgentSession(
            llm=pipeline["llm"],
            stt=pipeline.get("stt"),
            tts=pipeline.get("tts"),
            turn_handling=TurnHandlingOptions(
                turn_detection="vad",
                interruption={
                    "mode": "vad",
                    # Humanisierung Tier 1: min_duration 1.2 → 0.6 s.
                    # 1.2 s fühlte sich "taub" an — der Agent reagierte
                    # erst auf Barge-in nach über einer Sekunde. 0.6 s ist
                    # LiveKits Default, genug gegen Huster/Räuspern, aber
                    # so reaktiv, dass echte Unterbrechungen sofort
                    # greifen. resume_false_interruption fängt den Rest.
                    "min_duration": 0.6,
                    "resume_false_interruption": True,
                    # Phase 1 / Commit 3: false_interruption_timeout
                    # 2.0 → 1.0 s. Der Agent nimmt nach einer
                    # fälschlich erkannten Unterbrechung die Rede
                    # schneller wieder auf, was den Gesprächsfluss
                    # beschleunigt. 1.0 s ist immer noch lang genug,
                    # damit ein echtes Barge-in nicht überschrieben
                    # wird; darunter würden echte Unterbrechungen
                    # unterdrückt.
                    "false_interruption_timeout": 1.0,
                },
                preemptive_generation={
                    "enabled": False,
                    "preemptive_tts": True,
                    "max_speech_duration": 6.0,
                    "max_retries": 3,
                },
            ),
            vad=vad,
            tools=[frappe_toolset],
            tts_text_transforms=tts_transforms,
        )
    else:
        # type_b — external Mistral orchestrator owns the LLM+MCP turn loop.
        mistral_cfg = resolve_mistral_config()
        orchestrator = MistralOrchestrator(
            api_key=os.environ["MISTRAL_API_KEY"],
            agent_id=mistral_cfg["agent_id"],
            model=mistral_cfg["llm_model"],
            allowed_tools=allowed_tools,
            instructions=instructions,
            correlation_id=correlation_id,
        )
        session = AgentSession(
            llm=pipeline["llm"],  # NullLLM — opens the isinstance gate only
            stt=pipeline.get("stt"),
            tts=pipeline.get("tts"),
            turn_handling=TurnHandlingOptions(
                turn_detection="vad",
                interruption={
                    "mode": "vad",
                    # Humanisierung Tier 1: min_duration 1.2 → 0.6 s.
                    # 1.2 s fühlte sich "taub" an — der Agent reagierte
                    # erst auf Barge-in nach über einer Sekunde. 0.6 s ist
                    # LiveKits Default, genug gegen Huster/Räuspern, aber
                    # so reaktiv, dass echte Unterbrechungen sofort
                    # greifen. resume_false_interruption fängt den Rest.
                    "min_duration": 0.6,
                    "resume_false_interruption": True,
                    # Phase 1 / Commit 3: false_interruption_timeout
                    # 2.0 → 1.0 s. Der Agent nimmt nach einer
                    # fälschlich erkannten Unterbrechung die Rede
                    # schneller wieder auf, was den Gesprächsfluss
                    # beschleunigt. 1.0 s ist immer noch lang genug,
                    # damit ein echtes Barge-in nicht überschrieben
                    # wird; darunter würden echte Unterbrechungen
                    # unterdrückt.
                    "false_interruption_timeout": 1.0,
                },
                # preemptive_generation intentionally left at the LiveKit
                # default (disabled): the TTS stream comes from the external
                # Mistral orchestrator, not from a LiveKit LLM provider.
            ),
            vad=vad,
            # D-16: type_b routes every tool through the Mistral RunContext.
            # LiveKit-side tools must stay empty here — MistralDrivenAgent
            # .llm_node asserts this at turn time as a regression guard.
            tools=[],
            tts_text_transforms=tts_transforms,
        )
    
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
            if mode == "type_b":
                assert orchestrator is not None  # constructed in the type_b branch above
                agent = MistralDrivenAgent(
                    orchestrator=orchestrator,
                    instructions=instructions,
                    correlation_id=correlation_id,
                )
            else:
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
                "scheduling greeting task",
                extra={"correlation_id": correlation_id},
            )
            greeting_call_started = time.perf_counter()

            # Phase 1 / Commit 1: play greeting from cache if the
            # prewarm step synthesized it. Cache key is the fully
            # resolved greeting text, so any change to INITIAL_GREETING
            # or AGENT_NAME between prewarm and now correctly misses and
            # falls back to live synthesis. See
            # https://docs.livekit.io/agents/multimodality/audio/.
            cached_frames = ctx.proc.userdata.get("greeting_audio")
            cached_key = ctx.proc.userdata.get("greeting_audio_key")
            greeting_from_cache = bool(cached_frames) and cached_key == greeting

            async def _speak_greeting():
                t_say_start = time.perf_counter()
                try:
                    if greeting_from_cache:
                        logger.info(
                            "Greeting from cache",
                            extra={
                                "correlation_id": correlation_id,
                                "frame_count": len(cached_frames),
                            },
                        )

                        async def _frames_iter():
                            for frame in cached_frames:
                                yield frame

                        # Phase 1 follow-up fix: explicit
                        # allow_interruptions=True. Without it, LiveKit's
                        # default for session.say(audio=...) plays the
                        # pre-rendered frames uninterruptibly — the user
                        # reported „man kann sie nicht unterbrechen".
                        await session.say(
                            text=greeting,
                            audio=_frames_iter(),
                            allow_interruptions=True,
                        )
                    else:
                        logger.info(
                            "greeting_live_fallback",
                            extra={
                                "correlation_id": correlation_id,
                                "cache_present": cached_frames is not None,
                                "key_match": cached_key == greeting,
                            },
                        )
                        await session.say(greeting, allow_interruptions=True)
                except Exception:
                    logger.exception(
                        "greeting_say_failed",
                        extra={"correlation_id": correlation_id},
                    )
                    return
                t_tts_generate_ms = (time.perf_counter() - t_say_start) * 1000
                t_greeting_total_ms = (time.perf_counter() - greeting_flow_started) * 1000
                logger.info(
                    "greeting session.say returned",
                    extra={
                        "correlation_id": correlation_id,
                        "from_cache": greeting_from_cache,
                        "t_tts_first_audio_ms": round(t_tts_first_audio_ms, 2) if t_tts_first_audio_ms is not None else None,
                        "t_tts_first_chunk_ms": round(t_tts_first_chunk_ms, 2) if t_tts_first_chunk_ms is not None else None,
                        "t_tts_generate_ms": round(t_tts_generate_ms, 2),
                        "stt_retry_count": stt_retry_count,
                        "t_greeting_total_ms": round(t_greeting_total_ms, 2),
                    },
                )

            asyncio.create_task(_speak_greeting())
            t_session_start_to_greeting_call_ms = (greeting_call_started - greeting_flow_started) * 1000
            logger.info(
                "greeting_scheduled",
                extra={
                    "correlation_id": correlation_id,
                    "t_session_start_to_greeting_call_ms": round(t_session_start_to_greeting_call_ms, 2),
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
        # type_a: close the LiveKit MCPToolset from this disconnect-driven
        # task. type_b: deliberately NOT closed here — the Mistral
        # orchestrator owns an AsyncExitStack that was opened inside the
        # agent-activity task (via MistralDrivenAgent.on_enter →
        # orchestrator.initialize). Closing it from a fresh asyncio.Task
        # spawned by participant_disconnected triggers AnyIO's
        # cross-task cancel-scope guard and raises
        # RuntimeError("Attempted to exit cancel scope in a different task").
        # LiveKit's AgentActivity already invokes MistralDrivenAgent.on_exit
        # in the correct task on session teardown, which calls
        # orchestrator.aclose() cleanly.
        if frappe_toolset is not None:
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
