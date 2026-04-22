import json
import logging
import time
import asyncio
from typing import Any, Dict, Optional, List
from livekit.agents.voice.agent_session import AgentSession
from livekit.agents.llm.chat_context import ChatMessage
from livekit.agents.voice.events import ConversationItemAddedEvent

logger = logging.getLogger("agent.metrics")

def ensure_serializable(data: Any) -> Any:
    """Recursively ensures that data is JSON serializable, handling coroutines and other objects."""
    if isinstance(data, dict):
        return {k: ensure_serializable(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [ensure_serializable(v) for v in data]
    if asyncio.iscoroutine(data):
        return "<coroutine>"
    if isinstance(data, (int, float, str, bool, type(None))):
        return data
    # Handle Pydantic models or other objects with model_dump or __dict__
    if hasattr(data, "model_dump"):
        try:
            return ensure_serializable(data.model_dump(mode="json"))
        except:
            pass
    if hasattr(data, "__dict__"):
        return str(data)
    return str(data)

def log_metric(event_type: str, data: Dict[str, Any], level: int = logging.INFO):
    """Logs a structured metric in JSON format with 'METRIC:' prefix."""
    processed_data = {}
    for k, v in data.items():
        # Ensure all time values are integers (milliseconds) unless they are explicitly _s
        if k.endswith("_ms") and isinstance(v, (int, float)):
            processed_data[k] = int(round(v))
        elif k.endswith("_s") and isinstance(v, (int, float)):
            processed_data[k] = v # Keep as seconds if requested
        elif any(time_suffix in k for time_suffix in ["latency", "delay", "ttft", "ttfb", "duration"]) and isinstance(v, (int, float)):
            # Convert generic time fields to _ms if not already
            if k.endswith("_ms"):
                processed_data[k] = int(round(v))
            else:
                processed_data[f"{k}_ms"] = int(round(v * 1000))
        else:
            processed_data[k] = v
            
    # Remove any None values and ensure serializability
    final_data = {k: ensure_serializable(v) for k, v in processed_data.items() if v is not None}
    
    log_msg = f"METRIC: {json.dumps({'event': event_type, **final_data})}"
    logger.log(level, log_msg)

class MetricsListener:
    def __init__(self, session: AgentSession, correlation_id: str):
        self._session = session
        self._correlation_id = correlation_id
        self._turn_count = 0
        self._start_time = time.time()
        self._last_stt_duration_s: Optional[float] = None
        self._current_turn_gaps: List[float] = []
        
        self._attach_hooks()
        self._wrap_tts_if_present()

    def record_gap(self, gap_ms: float):
        """Records a gap between audio chunks."""
        self._current_turn_gaps.append(gap_ms)

    def _get_gap_metrics(self) -> Dict[str, int]:
        """Calculates avg, max, p95 for current turn gaps."""
        if not self._current_turn_gaps:
            return {
                "inter_chunk_gap_avg_ms": 0,
                "inter_chunk_gap_max_ms": 0,
                "inter_chunk_gap_p95_ms": 0,
            }
        
        gaps = sorted(self._current_turn_gaps)
        avg = sum(gaps) / len(gaps)
        mx = gaps[-1]
        # Simple p95 calculation
        p95_idx = max(0, int(0.95 * len(gaps)) - 1)
        p95 = gaps[p95_idx]
        
        return {
            "inter_chunk_gap_avg_ms": int(round(avg)),
            "inter_chunk_gap_max_ms": int(round(mx)),
            "inter_chunk_gap_p95_ms": int(round(p95)),
        }

    def _wrap_tts_if_present(self):
        """Wraps the TTS plugin to measure inter-chunk gaps if possible."""
        if not hasattr(self._session, "tts") or not self._session.tts:
            return
        
        tts = self._session.tts
        listener = self
        
        # Monkey-patch synthesize and stream to wrap returned streams
        if hasattr(tts, "synthesize"):
            orig_synthesize = tts.synthesize
            def wrapped_synthesize(*args, **kwargs):
                stream = orig_synthesize(*args, **kwargs)
                return self._wrap_stream(stream)
            tts.synthesize = wrapped_synthesize
            
        if hasattr(tts, "stream"):
            orig_stream = tts.stream
            def wrapped_stream(*args, **kwargs):
                stream = orig_stream(*args, **kwargs)
                return self._wrap_stream(stream)
            tts.stream = wrapped_stream

    def _wrap_stream(self, stream: Any) -> Any:
        """Wraps a ChunkedStream or SynthesizeStream to measure gaps."""
        listener = self
        
        class StreamWrapper:
            def __init__(self, original):
                self._original = original
                self._last_chunk_time = None
                
            def __getattr__(self, name):
                return getattr(self._original, name)
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                # We catch the result of the original __anext__
                chunk = await self._original.__anext__()
                now = time.perf_counter()
                if self._last_chunk_time is not None:
                    gap_ms = (now - self._last_chunk_time) * 1000
                    listener.record_gap(gap_ms)
                self._last_chunk_time = now
                return chunk
            
            async def __aenter__(self):
                if hasattr(self._original, "__aenter__"):
                    await self._original.__aenter__()
                return self
            
            async def __aexit__(self, exc_type, exc, tb):
                if hasattr(self._original, "__aexit__"):
                    return await self._original.__aexit__(exc_type, exc, tb)
                
        return StreamWrapper(stream)

    def _attach_hooks(self):
        # 1. Per-Turn-Metriken & 2. Conversation-Commit-Events
        @self._session.on("conversation_item_added")
        def on_item_added(event: ConversationItemAddedEvent):
            item = event.item
            if not isinstance(item, ChatMessage):
                return

            # Increment turn count for each user/assistant exchange
            if item.role in ["user", "assistant"]:
                self._turn_count += 1
            
            # 2. Conversation-Commit-Events
            text = item.text_content or ""
            commit_data = {
                "correlation_id": self._correlation_id,
                "turn_id": self._turn_count,
                "role": item.role,
                "text_length": len(text),
                "interrupted": item.interrupted,
                "timestamp": int(time.time() * 1000),
            }
            log_metric("conversation_item", commit_data)

            # 1. Per-Turn-Metriken (from item.metrics)
            if hasattr(item, "metrics") and item.metrics:
                m = item.metrics
                turn_data = {
                    "correlation_id": self._correlation_id,
                    "turn_id": self._turn_count,
                    "llm_ttft": m.get("llm_node_ttft"),
                    "tts_ttfb": m.get("tts_node_ttfb"),
                    "stt_duration": self._last_stt_duration_s, # will be converted to stt_duration_ms
                    "e2e_latency": m.get("e2e_latency"),
                    "end_of_turn_delay": m.get("end_of_turn_delay"),
                }
                
                # Add inter-chunk gap metrics if available (only for assistant)
                if item.role == "assistant":
                    turn_data.update(self._get_gap_metrics())
                    # Clear gaps for next turn
                    self._current_turn_gaps = []
                
                log_metric("turn_metrics", turn_data)
                
                # Reset STT duration for next turn
                if item.role == "assistant":
                    self._last_stt_duration_s = None

        # 3. Session-Ende & 4. Fehler-Events
        @self._session.on("close")
        def on_close(event):
            duration_s = time.time() - self._start_time
            
            # Safe session ID retrieval to avoid coroutine issues
            session_id = "unknown"
            try:
                room_io = getattr(self._session, "room_io", None)
                if room_io:
                    room = getattr(room_io, "room", None)
                    if room and hasattr(room, "sid"):
                        sid_val = room.sid
                        if not asyncio.iscoroutine(sid_val):
                            session_id = str(sid_val)
            except:
                pass

            session_data = {
                "correlation_id": self._correlation_id,
                "session_id": session_id,
                "duration_s": int(round(duration_s)),
                "turn_count": self._turn_count,
                "error_present": event.error is not None,
            }
            
            if event.error:
                error_source = str(getattr(event.error, "type", "UNKNOWN")).upper()
                error_recoverable = getattr(event.error, "recoverable", False)
                
                # Safely get error type name
                err_obj = getattr(event.error, "error", None)
                error_type = type(err_obj).__name__ if err_obj else "UnknownError"
                
                session_data.update({
                    "error_recoverable": error_recoverable,
                    "error_source": error_source,
                })
                
                # 4. Fehler-Events
                log_metric("error", {
                    "correlation_id": self._correlation_id,
                    "source": error_source,
                    "recoverable": error_recoverable,
                    "error_type": error_type,
                    "timestamp": int(time.time() * 1000),
                }, level=logging.ERROR if not error_recoverable else logging.WARNING)

            log_metric("session_end", session_data)

        # session_usage_updated for ongoing session usage
        @self._session.on("session_usage_updated")
        def on_usage_updated(event):
            for usage in event.usage.model_usage:
                usage_data = {
                    "correlation_id": self._correlation_id,
                    "provider": usage.provider,
                    "model": usage.model,
                }
                if hasattr(usage, "input_tokens"):
                    usage_data["input_tokens"] = usage.input_tokens
                if hasattr(usage, "output_tokens"):
                    usage_data["output_tokens"] = usage.output_tokens
                if hasattr(usage, "audio_duration"):
                    usage_data["audio_duration_ms"] = int(round(usage.audio_duration * 1000))
                
                log_metric("usage_update", usage_data)

        # Per-plugin metrics_collected for STT duration correlation
        self._register_plugin_metrics()
        
        # Realtime models emit metrics directly on the session
        @self._session.on("metrics_collected")
        def on_session_metrics(metrics):
            if metrics.type == "realtime_model_metrics":
                self._log_plugin_metric("RealtimeLLM", metrics)
            elif metrics.type == "stt_metrics":
                if hasattr(metrics, "audio_duration"):
                    self._last_stt_duration_s = metrics.audio_duration
                self._log_plugin_metric("STT", metrics)
            elif metrics.type == "tts_metrics":
                self._log_plugin_metric("TTS", metrics)
            else:
                self._log_plugin_metric("Session", metrics)

    def _register_plugin_metrics(self):
        # We try to catch STT audio duration specifically for turn metrics
        if self._session.stt and hasattr(self._session.stt, "on"):
            @self._session.stt.on("metrics_collected")
            def on_stt_metrics(metrics):
                if hasattr(metrics, "audio_duration"):
                    self._last_stt_duration_s = metrics.audio_duration
                
                # Also log detailed plugin metrics
                self._log_plugin_metric("STT", metrics)

        if self._session.tts and hasattr(self._session.tts, "on"):
            @self._session.tts.on("metrics_collected")
            def on_tts_metrics(metrics):
                self._log_plugin_metric("TTS", metrics)

        if self._session.llm and hasattr(self._session.llm, "on"):
            @self._session.llm.on("metrics_collected")
            def on_llm_metrics(metrics):
                self._log_plugin_metric("LLM", metrics)

    def _log_plugin_metric(self, label: str, metrics: Any):
        data = {
            "correlation_id": self._correlation_id,
            "plugin_label": label,
            "metrics_type": getattr(metrics, "type", "unknown"),
        }
        # Add numeric fields from the metrics object
        if hasattr(metrics, "model_dump"):
            dump = metrics.model_dump()
            for field, value in dump.items():
                if isinstance(value, (int, float)) and field not in ["timestamp"]:
                    data[field] = value
        
        log_metric("plugin_metrics", data)
