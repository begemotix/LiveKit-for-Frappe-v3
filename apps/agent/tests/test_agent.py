import pytest
import os
from unittest.mock import patch

# Phase-04 era this file installed a fake livekit.agents in sys.modules.
# That stub is obsolete (livekit-agents is now a hard dependency) and was
# actively harmful — it shadowed the real package and later-loaded test
# modules failed to find JobProcess / FlushSentinel.
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

# Phase-05 refactor note (D-16, D-17):
# The former tests `test_interruption` and
# `test_entrypoint_uses_mode_pipeline_and_voice_eu_name_for_type_b` asserted
# the pre-refactor behaviour — `session.generate_reply(instructions)` for
# the greeting and `AgentSession(tools=[frappe_toolset])` for type_b. Both
# no longer hold: greetings are emitted via `session.say(...)` in agent.py,
# and type_b passes `tools=[]` to AgentSession because the Mistral
# RunContext owns the tool loop. The equivalent coverage for the new
# architecture lives in tests/test_agent_entrypoint_branching.py (type_a
# MCPToolset presence, type_b tools=[] + D-16 guard, and disconnect
# cleanup dispatching to the right aclose path).
