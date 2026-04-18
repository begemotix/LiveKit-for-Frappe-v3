#!/usr/bin/env bash
# Erzeugt docker-compose.yml aus docker-compose.template.yml.
# Nur numerische Host-Ports aus der Umgebung (Coolify) — vermeidet invalid hostPort bei compose build.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TEMPLATE="$ROOT/docker-compose.template.yml"
OUT="$ROOT/docker-compose.yml"

export LIVEKIT_HOST_PORT_SIGNALING="${LIVEKIT_HOST_PORT_SIGNALING:-7880}"
export LIVEKIT_HOST_PORT_RTC_TCP="${LIVEKIT_HOST_PORT_RTC_TCP:-7881}"
export LIVEKIT_HOST_PORT_TURN_UDP="${LIVEKIT_HOST_PORT_TURN_UDP:-3478}"
export LIVEKIT_HOST_PORT_TURN_TLS="${LIVEKIT_HOST_PORT_TURN_TLS:-5349}"
export LIVEKIT_HOST_UDP_START="${LIVEKIT_HOST_UDP_START:-50000}"
export LIVEKIT_HOST_UDP_END="${LIVEKIT_HOST_UDP_END:-60000}"
export CADDY_HOST_PORT_HTTP="${CADDY_HOST_PORT_HTTP:-80}"
export CADDY_HOST_PORT_HTTPS="${CADDY_HOST_PORT_HTTPS:-443}"

require_uint() {
  local name="$1" val="$2"
  if [[ ! "$val" =~ ^[0-9]+$ ]] || [[ "$val" -gt 65535 ]]; then
    echo "render-compose: $name muss eine Ganzzahl 0–65535 sein (ist: $val)" >&2
    exit 1
  fi
}

require_uint LIVEKIT_HOST_PORT_SIGNALING "$LIVEKIT_HOST_PORT_SIGNALING"
require_uint LIVEKIT_HOST_PORT_RTC_TCP "$LIVEKIT_HOST_PORT_RTC_TCP"
require_uint LIVEKIT_HOST_PORT_TURN_UDP "$LIVEKIT_HOST_PORT_TURN_UDP"
require_uint LIVEKIT_HOST_PORT_TURN_TLS "$LIVEKIT_HOST_PORT_TURN_TLS"
require_uint LIVEKIT_HOST_UDP_START "$LIVEKIT_HOST_UDP_START"
require_uint LIVEKIT_HOST_UDP_END "$LIVEKIT_HOST_UDP_END"
require_uint CADDY_HOST_PORT_HTTP "$CADDY_HOST_PORT_HTTP"
require_uint CADDY_HOST_PORT_HTTPS "$CADDY_HOST_PORT_HTTPS"

if [[ "$LIVEKIT_HOST_UDP_END" -le "$LIVEKIT_HOST_UDP_START" ]]; then
  echo "render-compose: LIVEKIT_HOST_UDP_END muss größer als LIVEKIT_HOST_UDP_START sein" >&2
  exit 1
fi
local_span=$((LIVEKIT_HOST_UDP_END - LIVEKIT_HOST_UDP_START))
expected_span=$((60000 - 50000))
if [[ "$local_span" -ne "$expected_span" ]]; then
  echo "render-compose: UDP-Host-Spanne muss ${expected_span} sein (wie 50000–60000), ist: $local_span ($LIVEKIT_HOST_UDP_START–$LIVEKIT_HOST_UDP_END)" >&2
  exit 1
fi

if [[ ! -f "$TEMPLATE" ]]; then
  echo "render-compose: fehlt $TEMPLATE" >&2
  exit 1
fi

sed \
  -e "s/\$LIVEKIT_HOST_PORT_SIGNALING/$LIVEKIT_HOST_PORT_SIGNALING/g" \
  -e "s/\$LIVEKIT_HOST_PORT_RTC_TCP/$LIVEKIT_HOST_PORT_RTC_TCP/g" \
  -e "s/\$LIVEKIT_HOST_PORT_TURN_UDP/$LIVEKIT_HOST_PORT_TURN_UDP/g" \
  -e "s/\$LIVEKIT_HOST_PORT_TURN_TLS/$LIVEKIT_HOST_PORT_TURN_TLS/g" \
  -e "s/\$LIVEKIT_HOST_UDP_START/$LIVEKIT_HOST_UDP_START/g" \
  -e "s/\$LIVEKIT_HOST_UDP_END/$LIVEKIT_HOST_UDP_END/g" \
  -e "s/\$CADDY_HOST_PORT_HTTP/$CADDY_HOST_PORT_HTTP/g" \
  -e "s/\$CADDY_HOST_PORT_HTTPS/$CADDY_HOST_PORT_HTTPS/g" \
  "$TEMPLATE" > "$OUT"

echo "render-compose: $OUT (Signaling-Host $LIVEKIT_HOST_PORT_SIGNALING, UDP-Host $LIVEKIT_HOST_UDP_START–$LIVEKIT_HOST_UDP_END)" >&2
