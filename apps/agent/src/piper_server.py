"""Lifecycle manager for a local Piper HTTP server subprocess.

Usage pattern
-------------
Call ``ensure_piper_server()`` exactly once from the supervisor process
(``agent.py`` ``__main__`` block, before ``cli.run_app``). It:

1. downloads the requested voice model to ``data_dir`` if missing,
2. spawns ``python -m piper.http_server -m <voice> --data-dir ... --port ...``
   as a child process,
3. polls the ``GET /voices`` endpoint until ready (with backoff), and
4. returns the ``Popen`` handle so the supervisor keeps it alive for the
   container lifetime. The subprocess is terminated on normal exit via
   ``atexit``.

Design
------
- One Piper server per container, **not per worker**. Worker processes
  fork after ``cli.run_app`` and all reach the same ``localhost:<port>``
  via ``PIPER_BASE_URL``. Running one server per worker would require
  per-worker port allocation and duplicate ~100 MB of RAM per model.
- No async here on purpose: this runs before the asyncio event loop
  exists. Health checks use ``urllib.request`` with a plain sleep-loop.
- Download and server-start share the same ``python -m piper.*`` module
  entrypoints shipped by the ``piper-tts`` PyPI package.
"""
from __future__ import annotations

import atexit
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

logger = logging.getLogger("agent")

DEFAULT_VOICE = "de_DE-thorsten-high"
DEFAULT_DATA_DIR = "/tmp/piper_voices"
DEFAULT_PORT = 5000
_READINESS_TIMEOUT_S = 120
_READINESS_POLL_INTERVAL_S = 0.5

_server_process: subprocess.Popen | None = None


def ensure_piper_server(
    *,
    voice: str = DEFAULT_VOICE,
    data_dir: str = DEFAULT_DATA_DIR,
    port: int = DEFAULT_PORT,
) -> subprocess.Popen:
    """Start the Piper HTTP server if not already running. Idempotent."""
    global _server_process
    if _server_process is not None and _server_process.poll() is None:
        return _server_process

    Path(data_dir).mkdir(parents=True, exist_ok=True)

    if not _voice_files_present(voice, data_dir):
        logger.info(
            "piper_voice_download_started",
            extra={"voice": voice, "data_dir": data_dir},
        )
        _run_blocking(
            [
                sys.executable,
                "-m",
                "piper.download_voices",
                voice,
                "--data-dir",
                data_dir,
            ],
            step="download_voices",
        )
        logger.info("piper_voice_download_completed", extra={"voice": voice})

    logger.info(
        "piper_server_starting",
        extra={"voice": voice, "data_dir": data_dir, "port": port},
    )
    _server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "piper.http_server",
            "-m",
            voice,
            "--data-dir",
            data_dir,
            "--port",
            str(port),
            "--host",
            "127.0.0.1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    atexit.register(_terminate)

    _wait_until_ready(port)
    logger.info("piper_server_ready", extra={"port": port})
    return _server_process


def _voice_files_present(voice: str, data_dir: str) -> bool:
    root = Path(data_dir)
    return (root / f"{voice}.onnx").is_file() and (
        root / f"{voice}.onnx.json"
    ).is_file()


def _run_blocking(cmd: list[str], *, step: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(
            f"piper_{step}_failed",
            extra={
                "returncode": result.returncode,
                "stderr": result.stderr[-500:],
            },
        )
        raise RuntimeError(
            f"piper {step} failed with code {result.returncode}: {result.stderr[-500:]}"
        )


def _wait_until_ready(port: int) -> None:
    deadline = time.monotonic() + _READINESS_TIMEOUT_S
    last_err: str | None = None
    url = f"http://127.0.0.1:{port}/voices"
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=2) as resp:
                if 200 <= resp.status < 300:
                    return
                last_err = f"HTTP {resp.status}"
        except URLError as exc:
            last_err = repr(exc)
        except OSError as exc:
            last_err = repr(exc)
        time.sleep(_READINESS_POLL_INTERVAL_S)
    raise RuntimeError(
        f"Piper HTTP server did not become ready on port {port} "
        f"within {_READINESS_TIMEOUT_S}s; last error: {last_err}"
    )


def _terminate() -> None:
    global _server_process
    if _server_process is None:
        return
    if _server_process.poll() is None:
        _server_process.terminate()
        try:
            _server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _server_process.kill()
            _server_process.wait(timeout=5)
    _server_process = None


def _reset_for_tests() -> None:
    """Test hook — reset module state between unit tests."""
    global _server_process
    _server_process = None


def piper_base_url() -> str:
    """Resolve the Piper base URL for clients. Honors the PIPER_BASE_URL
    env var so staging/debug can point the agent at a remote Piper server
    without spawning a local subprocess."""
    return (
        (os.getenv("PIPER_BASE_URL") or "").strip()
        or f"http://127.0.0.1:{DEFAULT_PORT}"
    )
