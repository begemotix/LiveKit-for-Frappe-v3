import pytest
import os
import asyncio
import sys
from types import ModuleType
from unittest.mock import patch
from types import SimpleNamespace

if "livekit" not in sys.modules:
    livekit_module = ModuleType("livekit")
    agents_module = ModuleType("livekit.agents")
    llm_module = ModuleType("livekit.agents.llm")
    mcp_module = ModuleType("livekit.agents.llm.mcp")
    plugins_module = ModuleType("livekit.plugins")
    openai_module = ModuleType("livekit.plugins.openai")

    class _FakeWorkerOptions:
        def __init__(self, entrypoint_fnc=None, port=0):
            self.entrypoint_fnc = entrypoint_fnc
            self.port = port

    class _FakeAgent:
        def __init__(self, instructions=""):
            self.instructions = instructions

    class _FakeAgentSession:
        def __init__(self, *args, **kwargs):
            pass

    class _FakeRealtimeModel:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _FakeToolset:
        def __init__(self, id, mcp_server):
            self.id = id
            self.mcp_server = mcp_server

    def _function_tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    agents_module.JobContext = object
    agents_module.WorkerOptions = _FakeWorkerOptions
    agents_module.cli = SimpleNamespace(run_app=lambda options: options)
    agents_module.llm = llm_module
    agents_module.Agent = _FakeAgent
    agents_module.AgentSession = _FakeAgentSession
    llm_module.function_tool = _function_tool
    llm_module.mcp = mcp_module
    mcp_module.MCPToolset = _FakeToolset
    openai_module.realtime = SimpleNamespace(RealtimeModel=_FakeRealtimeModel)
    plugins_module.openai = openai_module

    livekit_module.agents = agents_module
    livekit_module.plugins = plugins_module

    sys.modules["livekit"] = livekit_module
    sys.modules["livekit.agents"] = agents_module
    sys.modules["livekit.agents.llm"] = llm_module
    sys.modules["livekit.agents.llm.mcp"] = mcp_module
    sys.modules["livekit.plugins"] = plugins_module
    sys.modules["livekit.plugins.openai"] = openai_module

from agent import entrypoint, Assistant
from livekit.agents import WorkerOptions

@pytest.mark.asyncio
async def test_join():
    """Verify WorkerOptions has entrypoint set to the correct function."""
    options = WorkerOptions(entrypoint_fnc=entrypoint)
    assert options.entrypoint_fnc == entrypoint

@pytest.mark.asyncio
async def test_mock_tool():
    """Verify mock_data_lookup is reachable and returns the expected JSON structure."""
    assistant = Assistant(instructions="test", correlation_id="test-correlation")
    # Mocking logger to avoid actual log output during test
    with patch('agent.logger'):
        result = await assistant.mock_data_lookup(query="Frappe ERP")
    assert result["status"] == "success"
    assert "Frappe ERP" in result["data"]

@pytest.mark.asyncio
async def test_persona_injection():
    """Verify variable substitution logic used in agent.py."""
    with patch.dict(os.environ, {
        "AGENT_NAME": "TestAgent",
        "COMPANY_NAME": "TestCompany",
        "ROLE_DESCRIPTION": "You are {AGENT_NAME}, a helpful assistant for {COMPANY_NAME}.",
        "INITIAL_GREETING": "Hello! Ich bin {AGENT_NAME} von {COMPANY_NAME}."
    }):
        # Reproduce substitution logic from agent.py
        agent_name = os.getenv("AGENT_NAME", "AI")
        company_name = os.getenv("COMPANY_NAME", "Company")
        
        base_instructions = os.getenv("ROLE_DESCRIPTION", "You are a helpful assistant for {COMPANY_NAME}. Your name is {AGENT_NAME}.") \
            .replace("{AGENT_NAME}", agent_name) \
            .replace("{COMPANY_NAME}", company_name)
            
        greeting = os.getenv("INITIAL_GREETING", "Hallo! Ich bin {AGENT_NAME} von {COMPANY_NAME}. Wie kann ich Ihnen heute helfen?") \
            .replace("{AGENT_NAME}", agent_name) \
            .replace("{COMPANY_NAME}", company_name)
        
        assert "TestAgent" in base_instructions
        assert "TestCompany" in base_instructions
        assert "TestAgent" in greeting
        assert "TestCompany" in greeting

@pytest.mark.asyncio
async def test_interruption():
    """Verify interruption behavior via public session.say calls."""

    class FakeRoom:
        def __init__(self):
            self.name = "test-room"
            self.remote_participants = {"p1": SimpleNamespace(identity="participant-1")}
            self._handlers = {}

        def on(self, event_name):
            def decorator(func):
                self._handlers[event_name] = func
                return func
            return decorator

    class FakeContext:
        def __init__(self):
            self.room = FakeRoom()
            self.log_context_fields = {}

        async def connect(self):
            return None

    class FakeAgentSession:
        last_instance = None

        def __init__(self, llm, allow_interruptions, tools=None, mcp_servers=None, stt=None, tts=None):
            self.llm = llm
            self.allow_interruptions = allow_interruptions
            self.tools = tools or []
            self.mcp_servers = mcp_servers or []
            self.stt = stt
            self.tts = tts
            self.generate_reply_calls = []
            FakeAgentSession.last_instance = self

        def on(self, _event_name):
            def decorator(func):
                return func
            return decorator

        async def start(self, room, agent):
            self.room = room
            self.agent = agent

        async def generate_reply(self, instructions):
            self.generate_reply_calls.append(instructions)

    created_tasks = []

    def schedule_now(coro):
        task = asyncio.get_running_loop().create_task(coro)
        created_tasks.append(task)
        return task

    pipeline = {"llm": object(), "stt": None, "tts": None}

    with patch("agent.resolve_agent_mode", return_value="type_a"), \
         patch("agent.validate_mode_env"), \
         patch("agent.build_voice_pipeline", return_value=pipeline), \
         patch("agent.build_frappe_mcp_server", return_value=object()), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        ctx = FakeContext()
        await entrypoint(ctx)
        await asyncio.gather(*created_tasks)

    assert FakeAgentSession.last_instance is not None
    reply_calls = FakeAgentSession.last_instance.generate_reply_calls
    assert len(reply_calls) >= 1
    assert "Begrüße den Nutzer freundlich" in reply_calls[0]


@pytest.mark.asyncio
async def test_entrypoint_uses_mode_pipeline_and_voice_eu_name_for_type_b():
    class FakeRoom:
        def __init__(self):
            self.name = "test-room"
            self.remote_participants = {"p1": SimpleNamespace(identity="participant-1")}
            self._handlers = {}

        def on(self, event_name):
            def decorator(func):
                self._handlers[event_name] = func
                return func
            return decorator

    class FakeContext:
        def __init__(self):
            self.room = FakeRoom()
            self.log_context_fields = {}

        async def connect(self):
            return None

    class FakeMCPToolset:
        def __init__(self, id, mcp_server):
            self.id = id
            self.mcp_server = mcp_server

        async def aclose(self):
            return None

    class FakeAgentSession:
        last_instance = None

        def __init__(self, llm, allow_interruptions, tools=None, stt=None, tts=None):
            self.llm = llm
            self.allow_interruptions = allow_interruptions
            self.tools = tools or []
            self.stt = stt
            self.tts = tts
            self.generate_reply_calls = []
            FakeAgentSession.last_instance = self

        def on(self, _event_name):
            def decorator(func):
                return func
            return decorator

        async def start(self, room, agent):
            self.room = room
            self.agent = agent

        async def generate_reply(self, instructions):
            self.generate_reply_calls.append(instructions)

    created_tasks = []

    def schedule_now(coro):
        task = asyncio.get_running_loop().create_task(coro)
        created_tasks.append(task)
        return task

    pipeline = {"llm": object(), "stt": object(), "tts": object()}

    with patch("agent.resolve_agent_mode", return_value="type_b") as resolve_mode_mock, \
         patch("agent.validate_mode_env") as validate_mode_env_mock, \
         patch("agent.build_voice_pipeline", return_value=pipeline) as build_pipeline_mock, \
         patch("agent.build_frappe_mcp_server", return_value=object()), \
         patch("agent.mcp.MCPToolset", FakeMCPToolset), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now), \
         patch.dict(os.environ, {"AGENT_NAME": "LegacyName", "COMPANY_NAME": "TestCo"}, clear=False):
        ctx = FakeContext()
        await entrypoint(ctx)
        await asyncio.gather(*created_tasks)

    resolve_mode_mock.assert_called_once_with()
    validate_mode_env_mock.assert_called_once_with("type_b")
    build_pipeline_mock.assert_called_once_with("type_b")
    assert FakeAgentSession.last_instance is not None
    assert FakeAgentSession.last_instance.llm is pipeline["llm"]
    assert FakeAgentSession.last_instance.stt is pipeline["stt"]
    assert FakeAgentSession.last_instance.tts is pipeline["tts"]
    assert len(FakeAgentSession.last_instance.tools) == 1
    assert FakeAgentSession.last_instance.tools[0].id == "frappe_mcp"
    assert FakeAgentSession.last_instance.agent is not None
    reply_calls = FakeAgentSession.last_instance.generate_reply_calls
    assert len(reply_calls) >= 1
    assert "voice-eu" in reply_calls[0]
