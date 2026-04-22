import json
import logging
import time
from typing import Any, Dict, Optional
from livekit.agents.voice.agent_session import AgentSession
from livekit.agents.llm.chat_context import ChatMessage
from livekit.agents.voice.events import ConversationItemAddedEvent

logger = logging.getLogger("agent.metrics")

def log_metric(event_type: str, data: Dict[str, Any], level: int = logging.INFO):
    """Logs a structured metric in JSON format with 'METRIC:' prefix."""
    # Ensure all time values are integers (milliseconds) unless they are explicitly _s
    processed_data = {}
    for k, v in data.items():
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
            
    # Remove any None values from the log
    processed_data = {k: v for k, v in processed_data.items() if v is not None}
    
    log_msg = f"METRIC: {json.dumps({'event': event_type, **processed_data})}"
    logger.log(level, log_msg)

class MetricsListener:
    def __init__(self, session: AgentSession, correlation_id: str):
        self._session = session
        self._correlation_id = correlation_id
        self._turn_count = 0
        self._start_time = time.time()
        self._last_stt_duration_s: Optional[float] = None
        
        self._attach_hooks()

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
                    "stt_duration_ms": self._last_stt_duration_s * 1000 if self._last_stt_duration_s is not None else None,
                    "e2e_latency": m.get("e2e_latency"),
                    "end_of_turn_delay": m.get("end_of_turn_delay"),
                }
                # Filter out None values and log
                log_metric("turn_metrics", turn_data)
                # Reset STT duration for next turn
                if item.role == "assistant":
                    self._last_stt_duration_s = None

        # 3. Session-Ende & 4. Fehler-Events
        @self._session.on("close")
        def on_close(event):
            duration_s = time.time() - self._start_time
            session_data = {
                "correlation_id": self._correlation_id,
                "session_id": getattr(self._session.room_io.room, "sid", "unknown") if hasattr(self._session, "room_io") else "unknown",
                "duration_s": int(round(duration_s)),
                "turn_count": self._turn_count,
                "error_present": event.error is not None,
            }
            
            if event.error:
                error_source = str(getattr(event.error, "type", "UNKNOWN")).upper()
                error_recoverable = getattr(event.error, "recoverable", False)
                error_type = type(event.error.error).__name__ if hasattr(event.error, "error") and event.error.error else "UnknownError"
                
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
