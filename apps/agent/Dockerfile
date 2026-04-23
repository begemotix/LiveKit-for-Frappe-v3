# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System-Abhängigkeiten für WebRTC/Audio + Node fuer Frappe-MCP-stdio-Sidecar.
#
# WICHTIG: Node/npm kommen von NodeSource, nicht aus den Debian-Repos.
# Debians `npm`-Paket zieht ~671 Transitive (LLVM, X11, HEIF/AVIF-Codecs,
# Fonts, GnuPG, Perl …) → 941 MB Layer, Build > 10 Min, Coolify-Timeout
# (siehe Deploy-Log vom 2026-04-23). NodeSource liefert ein einziges
# `nodejs`-Paket mit gebündeltem npm; das Image bleibt schlank und der
# Build passt in Coolifys 10-Minuten-Fenster.
#
# --no-install-recommends hält den Rest frei von optionalem Ballast.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3-dev \
        curl \
        ca-certificates \
        gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Frappe MCP fest im Image installieren (kein npx Cold-Start zur Laufzeit).
#
# --prefix=/usr/local ist essentiell: NodeSource-npm installiert global
# standardmäßig nach /usr/bin/, aber der Rest des Projekts (ENV unten,
# src/frappe_mcp.py:80, tests/test_frappe_mcp_helpers.py:46,52) erwartet
# das Binary unter /usr/local/bin/frappe-mcp-server. Mit dem Prefix-Flag
# bleibt der Pfad-Vertrag identisch zur alten Debian-apt-Variante.
RUN npm install -g --prefix=/usr/local frappe-mcp-server \
    && command -v frappe-mcp-server
ENV FRAPPE_MCP_BINARY=/usr/local/bin/frappe-mcp-server

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Start-Kommando (Agent worker)
CMD ["python", "agent.py", "start"]
