"""Unit tests for the Piper HTTP server subprocess lifecycle.

We mock ``subprocess.run`` (for the voice download step), ``subprocess.Popen``
(for the HTTP server process), and the readiness poll so nothing actually
touches the network or disk. The tests pin the behaviour we rely on in
production:

- Skipping the download when the voice files already exist on disk.
- Calling the right ``python -m piper.download_voices`` command when they
  don't.
- Spawning ``python -m piper.http_server`` with the expected flags.
- Polling ``/voices`` until the server answers 200.
- Being idempotent — a second call returns the same Popen handle.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import src.piper_server as piper_server


@pytest.fixture(autouse=True)
def _reset_module_state():
    piper_server._reset_for_tests()
    yield
    piper_server._reset_for_tests()


def _install_urlopen_ok(monkeypatch: pytest.MonkeyPatch):
    """Make the readiness poll return 200 on the first call."""
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = MagicMock(status=200)
    mock_ctx.__exit__.return_value = False
    mock_urlopen = MagicMock(return_value=mock_ctx)
    monkeypatch.setattr(piper_server, "urlopen", mock_urlopen)
    return mock_urlopen


def test_ensure_starts_server_and_downloads_missing_voice(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    data_dir = tmp_path / "voices"
    # voice files do not exist yet → download step must run
    fake_popen = MagicMock()
    fake_popen.poll.return_value = None
    monkeypatch.setattr(piper_server.subprocess, "Popen", MagicMock(return_value=fake_popen))

    fake_run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    monkeypatch.setattr(piper_server.subprocess, "run", fake_run)

    _install_urlopen_ok(monkeypatch)

    result = piper_server.ensure_piper_server(
        voice="de_DE-thorsten-high", data_dir=str(data_dir), port=5555
    )

    assert result is fake_popen
    assert fake_run.call_count == 1
    download_cmd = fake_run.call_args.args[0]
    assert download_cmd[1:5] == ["-m", "piper.download_voices", "de_DE-thorsten-high", "--data-dir"]
    assert download_cmd[5] == str(data_dir)

    popen_cmd = piper_server.subprocess.Popen.call_args.args[0]
    assert popen_cmd[1:6] == ["-m", "piper.http_server", "-m", "de_DE-thorsten-high", "--data-dir"]
    # port + host flags appear after --data-dir <dir>
    assert "--port" in popen_cmd and "5555" in popen_cmd
    assert "--host" in popen_cmd and "127.0.0.1" in popen_cmd


def test_ensure_skips_download_when_voice_files_exist(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    data_dir = tmp_path / "voices"
    data_dir.mkdir()
    (data_dir / "de_DE-thorsten-high.onnx").write_bytes(b"")
    (data_dir / "de_DE-thorsten-high.onnx.json").write_bytes(b"{}")

    fake_popen = MagicMock()
    fake_popen.poll.return_value = None
    monkeypatch.setattr(piper_server.subprocess, "Popen", MagicMock(return_value=fake_popen))

    fake_run = MagicMock()
    monkeypatch.setattr(piper_server.subprocess, "run", fake_run)

    _install_urlopen_ok(monkeypatch)

    piper_server.ensure_piper_server(
        voice="de_DE-thorsten-high", data_dir=str(data_dir), port=5555
    )

    fake_run.assert_not_called()


def test_ensure_is_idempotent(tmp_path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "voices"
    data_dir.mkdir()
    (data_dir / "de_DE-thorsten-high.onnx").write_bytes(b"")
    (data_dir / "de_DE-thorsten-high.onnx.json").write_bytes(b"{}")

    fake_popen = MagicMock()
    fake_popen.poll.return_value = None
    popen_mock = MagicMock(return_value=fake_popen)
    monkeypatch.setattr(piper_server.subprocess, "Popen", popen_mock)
    _install_urlopen_ok(monkeypatch)

    p1 = piper_server.ensure_piper_server(data_dir=str(data_dir))
    p2 = piper_server.ensure_piper_server(data_dir=str(data_dir))

    assert p1 is p2
    # Popen was called exactly once
    assert popen_mock.call_count == 1


def test_download_failure_raises(tmp_path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "voices"
    monkeypatch.setattr(piper_server.subprocess, "Popen", MagicMock())

    fake_run = MagicMock(return_value=MagicMock(returncode=1, stderr="network oops"))
    monkeypatch.setattr(piper_server.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="download_voices"):
        piper_server.ensure_piper_server(data_dir=str(data_dir))


def test_piper_base_url_honors_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PIPER_BASE_URL", "http://some-other-host:9999/")
    # strip trailing slash normalisation lives in PiperTTS, not here; the
    # env-read is verbatim. Consumers must tolerate the trailing slash.
    assert piper_server.piper_base_url() == "http://some-other-host:9999/"


def test_piper_base_url_defaults_to_localhost(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PIPER_BASE_URL", raising=False)
    assert piper_server.piper_base_url() == "http://127.0.0.1:5000"
