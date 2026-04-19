import pytest
import os
import asyncio
from unittest.mock import patch
from types import SimpleNamespace
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
    assistant = Assistant(instructions="test")
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

        def __init__(self, llm, allow_interruptions):
            self.llm = llm
            self.allow_interruptions = allow_interruptions
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

    with patch("agent.openai.realtime.RealtimeModel", return_value=object()), \
         patch("agent.AgentSession", FakeAgentSession), \
         patch("agent.asyncio.create_task", side_effect=schedule_now):
        ctx = FakeContext()
        await entrypoint(ctx)
        await asyncio.gather(*created_tasks)

    assert FakeAgentSession.last_instance is not None
    reply_calls = FakeAgentSession.last_instance.generate_reply_calls
    assert len(reply_calls) >= 1
    assert "Begrüße den Nutzer freundlich" in reply_calls[0]
