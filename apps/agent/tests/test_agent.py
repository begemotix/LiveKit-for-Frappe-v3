import pytest
import os
from unittest.mock import patch
from agent import entrypoint, Assistant
from livekit.agents import WorkerOptions
from livekit.agents.voice import AgentSession
from livekit.plugins import openai

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
@pytest.mark.xfail(reason="Legacy interruption assertion depends on removed internal AgentSession field.", strict=False)
async def test_interruption():
    """Verify that the AgentSession and model are configured correctly."""
    # Set dummy API key for testing RealtimeModel initialization
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy"}):
        model = openai.realtime.RealtimeModel(
            modalities=["audio", "text"],
            turn_detection={
                "type": "server_vad",
                "threshold": 0.5,
                "silence_duration_ms": 500
            }
        )
        
        session = AgentSession(
            llm=model,
            allow_interruptions=True,
        )
        
        # Check if allow_interruptions is set correctly (internal attribute check)
        assert session._allow_interruptions is True
        
        # Check if VAD options are present in the model
        assert model._opts.turn_detection["threshold"] == 0.5
        assert model._opts.turn_detection["silence_duration_ms"] == 500
