"""
Verification test suite for all benchmark targets and in-memory routes.
Validates that Dreaming Electric Sheep (default & ceiling), Granian Raw, Uvicorn Raw,
Emmett, Sanic, FastAPI, Litestar, and Robyn all correctly implement the endpoints.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    {
        "name": "Granian Raw RSGI",
        "type": "granian_rsgi",
        "module": "perf.compare.granian_raw_rsgi_app:app",
        "requires": ["granian"],
    },
    {
        "name": "Granian Raw ASGI",
        "type": "granian",
        "module": "perf.compare.granian_raw_app:app",
        "requires": ["granian"],
    },
    {
        "name": "Dreaming Electric Sheep (RSGI)",
        "type": "granian_rsgi",
        "module": "perf.compare.des_app:app",
        "requires": ["granian"],
    },
    {
        "name": "Dreaming Electric Sheep (Default ASGI)",
        "type": "granian",
        "module": "perf.compare.des_app:app",
        "requires": ["granian"],
    },
    {
        "name": "Dreaming Electric Sheep (Ceiling)",
        "type": "granian",
        "module": "perf.compare.des_ceiling_app:app",
        "requires": ["granian"],
    },
    {
        "name": "Uvicorn Raw ASGI",
        "type": "uvicorn",
        "module": "perf.compare.uvicorn_raw_app:app",
        "requires": ["uvicorn"],
    },
    {
        "name": "Emmett",
        "type": "granian",
        "module": "perf.compare.emmett_app:app",
        "requires": ["granian", "emmett"],
    },
    {
        "name": "Sanic",
        "type": "sanic",
        "command": [
            sys.executable,
            "-m",
            "sanic",
            "perf.compare.sanic_app:app",
            "-H", "127.0.0.1",
            "-p", "{port}",
            "-w", "1",
            "--no-access-logs",
            "--no-motd",
        ],
        "requires": ["sanic"],
    },
    {
        "name": "FastAPI",
        "type": "granian",
        "module": "perf.compare.fastapi_app:app",
        "requires": ["granian", "fastapi"],
    },
    {
        "name": "Litestar",
        "type": "granian",
        "module": "perf.compare.litestar_app:app",
        "requires": ["granian", "litestar"],
    },
    {
        "name": "Robyn",
        "type": "standalone",
        "command": [
            sys.executable,
            str(REPO_ROOT / "perf" / "compare" / "robyn_app.py"),
            "--port", "{port}",
            "--processes", "1",
            "--workers", "1",
            "--log-level", "WARN",
            "--disable-openapi",
        ],
        "requires": ["robyn"],
    },
    {
        "name": "Flask",
        "type": "granian_wsgi",
        "module": "perf.compare.flask_app:app",
        "requires": ["granian", "flask"],
    },
    {
        "name": "Django",
        "type": "granian_wsgi",
        "module": "perf.compare.django_app:app",
        "requires": ["granian", "django"],
    },
]


_GRANIAN_BIN = shutil.which("granian") or str(Path(sys.executable).parent / "granian")
_GRANIAN_AVAILABLE = shutil.which("granian") is not None or Path(_GRANIAN_BIN).exists()

pytestmark_bench = pytest.mark.skipif(
    not _GRANIAN_AVAILABLE,
    reason="granian binary not found; install granian to run benchmark smoke tests",
)


def wait_for_server(url: str, timeout: float = 10.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False


@pytestmark_bench
@pytest.mark.parametrize("target", TARGETS, ids=[t["name"] for t in TARGETS])
def test_benchmark_app_routes(target, unused_tcp_port):
    # Skip immediately if any required package is not installed
    for pkg in target.get("requires", []):
        try:
            __import__(pkg)
        except ImportError:
            pytest.skip(f"Required package '{pkg}' not installed")

    port = unused_tcp_port
    host = "127.0.0.1"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    for k in list(env.keys()):
        if k.startswith("APP_"):
            del env[k]

    venv_bin = Path(sys.executable).parent
    granian_bin = _GRANIAN_BIN
    uvicorn_bin = shutil.which("uvicorn") or str(venv_bin / "uvicorn")

    t_type = target["type"]
    if t_type == "granian":
        cmd = [
            granian_bin,
            "--interface", "asgi",
            "--host", host,
            "--port", str(port),
            "--workers", "1",
            target["module"],
        ]
    elif t_type == "granian_rsgi":
        cmd = [
            granian_bin,
            "--interface", "rsgi",
            "--host", host,
            "--port", str(port),
            "--workers", "1",
            target["module"],
        ]
    elif t_type == "granian_wsgi":
        cmd = [
            granian_bin,
            "--interface", "wsgi",
            "--host", host,
            "--port", str(port),
            "--workers", "1",
            target["module"],
        ]
    elif t_type == "uvicorn":
        cmd = [
            uvicorn_bin,
            target["module"],
            "--host", host,
            "--port", str(port),
            "--workers", "1",
            "--no-access-log",
        ]
    elif t_type in ("sanic", "standalone"):
        cmd = [arg.format(port=port) for arg in target["command"]]

    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        base_url = f"http://{host}:{port}"
        assert wait_for_server(f"{base_url}/plaintext", timeout=12.0), f"{target['name']} failed to start"

        # 1. Plaintext
        with urllib.request.urlopen(f"{base_url}/plaintext") as resp:
            assert resp.status == 200
            assert "text/plain" in resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
            assert body == "Hello, World!"

        # 2. JSON
        with urllib.request.urlopen(f"{base_url}/json") as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers.get("Content-Type", "")
            data = json.loads(resp.read())
            assert data == {"message": "Hello, World!"}

        # 3. Single query /db
        with urllib.request.urlopen(f"{base_url}/db") as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert "id" in data and "randomNumber" in data
            assert 1 <= data["id"] <= 10000

        # 4. Multiple queries /queries?queries=5
        with urllib.request.urlopen(f"{base_url}/queries?queries=5") as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert isinstance(data, list)
            assert len(data) == 5
            for item in data:
                assert "id" in item and "randomNumber" in item

        # 5. Fortunes /fortunes
        with urllib.request.urlopen(f"{base_url}/fortunes") as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
            html_text = resp.read().decode("utf-8")
            assert "<table>" in html_text
            assert "Additional fortune added at request time." in html_text
            assert "&lt;script&gt;" in html_text

        # 6. Data updates /updates?queries=5
        with urllib.request.urlopen(f"{base_url}/updates?queries=5") as resp:
            assert resp.status == 200
            data = json.loads(resp.read())
            assert isinstance(data, list)
            assert len(data) == 5

    finally:
        shutdown_signal = None
        for sig_name in ("SIGINT", "SIGTERM"):
            sig = getattr(signal, sig_name, None)
            if sig is None:
                continue
            try:
                signal.getsignal(sig)
                shutdown_signal = sig
                break
            except (AttributeError, ValueError, OSError):
                continue

        if shutdown_signal is not None:
            try:
                proc.send_signal(shutdown_signal)
            except (ValueError, OSError):
                pass
        else:
            try:
                proc.terminate()
            except OSError:
                pass

        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        time.sleep(0.5)
