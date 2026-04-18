---
phase: 03-agent-core
plan: 01
subsystem: agent-worker
tags: [setup, configuration, logging]
requirements: [AGNT-01]
key-files:
  - apps/agent/requirements.txt
  - apps/agent/.env.example
  - apps/agent/agent.py
decisions:
  - D-01: Dynamische Persona-Konfiguration via ENV
  - D-09: Strukturiertes JSON-Logging
  - D-10: Korrelations-ID aus Room-Name
metrics:
  duration: 10m
  completed_date: 2026-04-18
---

# Phase 03 Plan 01: Agent Base & Configuration Summary

## Objective
Setup the foundation for the Python Agent Worker, including directory structure, dependencies, and configuration interface via environment variables.

## Key Changes

### Agent Directory Initialization
- Cloned official `agent-starter-python` template.
- Decoupled from upstream by removing `.git`.
- Restructured template to match project requirements (moved `agent.py` to root).

### Configuration & Dependencies
- Created `requirements.txt` with specific versions:
  - `livekit-agents[openai]~=1.4.0`
  - `python-json-logger~=2.0.0`
  - `python-dotenv~=1.0.0`
- Defined `.env.example` with comprehensive white-labeling and VAD configuration.

### Core Skeleton & Logging
- Implemented `agent.py` using `WorkerOptions` and `entrypoint`.
- Initialized structured JSON logging using `python-json-logger`.
- Implemented correlation ID derivation from LiveKit room name for session tracking.

## Deviations from Plan
- **Template Structure**: The cloned template used a `src/` directory and `pyproject.toml`. I moved `agent.py` to the root and created `requirements.txt` to align strictly with the plan's file structure and requirements.

## Self-Check: PASSED
- [x] Directory `apps/agent` exists.
- [x] `requirements.txt` contains correct library versions.
- [x] `.env.example` reflects all required white-labeling variables.
- [x] `agent.py` exists with structured logging initialized.
- [x] All commits made with `--no-verify`.
