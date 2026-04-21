# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System-Abhängigkeiten für WebRTC/Audio + Node fuer Frappe-MCP-stdio-Sidecar
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Frappe MCP fest im Image installieren (kein npx Cold-Start zur Laufzeit)
RUN npm install -g frappe-mcp-server \
    && command -v frappe-mcp-server
ENV FRAPPE_MCP_BINARY=/usr/local/bin/frappe-mcp-server

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Start-Kommando (Agent worker)
CMD ["python", "agent.py", "start"]
