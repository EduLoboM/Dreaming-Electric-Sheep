#!/usr/bin/env python3
"""
Honest ASGI / Rust runtime framework benchmark runner for:
Dreaming Electric Sheep vs Robyn vs Litestar vs FastAPI.
Runs each framework under 1 worker / 1 process and measures
true throughput & latency with oha (Rust HTTP load tester).
"""
import sys
import os
import time
import json
import shutil
import signal
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
COMPARE_DIR = Path(__file__).resolve().parent

FRAMEWORKS = [
    {
        "name": "Dreaming Electric Sheep",
        "type": "granian",
        "module": "perf.compare.des_app:app",
    },
    {
        "name": "Robyn",
        "type": "standalone",
        "command": [
            sys.executable,
            str(COMPARE_DIR / "robyn_app.py"),
            "--processes", "1",
            "--workers", "1",
            "--log-level", "WARN",
            "--disable-openapi",
        ],
    },
    {
        "name": "Litestar",
        "type": "granian",
        "module": "perf.compare.litestar_app:app",
    },
    {
        "name": "FastAPI",
        "type": "granian",
        "module": "perf.compare.fastapi_app:app",
    },
]

ROUTES = [
    {"path": "/plaintext", "name": "plaintext"},
    {"path": "/json", "name": "json"},
]


def find_oha() -> str:
    oha_path = shutil.which("oha")
    if not oha_path:
        local_venv_oha = WORKSPACE_ROOT / ".venv" / "bin" / "oha"
        if local_venv_oha.exists():
            oha_path = str(local_venv_oha)
    if not oha_path:
        print("ERROR: 'oha' load tester was not found in PATH or .venv/bin/oha.", file=sys.stderr)
        print("Please install oha (e.g. pacman -S oha, cargo install oha, or download prebuilt binary).", file=sys.stderr)
        sys.exit(1)
    return oha_path


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


def run_oha_bench(
    oha_bin: str,
    url: str,
    duration_s: int = 10,
    concurrency: int = 50,
) -> Dict[str, Any]:
    cmd = [
        oha_bin,
        "--no-tui",
        "--output-format", "json",
        "-z", f"{duration_s}s",
        "-c", str(concurrency),
        "-w",
        url,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"oha failed (code {proc.returncode}): {proc.stderr}")

    try:
        data = json.loads(proc.stdout)
    except Exception as e:
        raise RuntimeError(f"Failed to parse oha JSON output: {e}\nRaw output:\n{proc.stdout}")

    rps = data.get("summary", {}).get("requestsPerSec", 0.0)
    lat_p50_s = data.get("latencyPercentiles", {}).get("p50", 0.0) or 0.0
    lat_p99_s = data.get("latencyPercentiles", {}).get("p99", 0.0) or 0.0
    errors_dict = data.get("errorDistribution", {})
    error_count = sum(errors_dict.values()) if isinstance(errors_dict, dict) else 0

    # Convert latencies to ms
    p50_ms = lat_p50_s * 1000.0
    p99_ms = lat_p99_s * 1000.0

    return {
        "rps": round(rps, 2),
        "p50_ms": round(p50_ms, 3),
        "p99_ms": round(p99_ms, 3),
        "errors": error_count,
    }


def main():
    oha_bin = find_oha()
    granian_bin = shutil.which("granian") or str(WORKSPACE_ROOT / ".venv" / "bin" / "granian")

    if not Path(granian_bin).exists() and not shutil.which(granian_bin):
        print(f"ERROR: 'granian' ASGI server not found at {granian_bin}.", file=sys.stderr)
        sys.exit(1)

    port = 8000
    host = "127.0.0.1"
    duration = 10
    concurrency = 50

    results: List[Dict[str, Any]] = []

    print(f"Starting comparison benchmarks using oha ({oha_bin})...")
    print(f"Duration per run: {duration}s | Concurrency: {concurrency} | Workers: 1\n")

    for fw in FRAMEWORKS:
        name = fw["name"]
        fw_type = fw["type"]
        print(f"--- Benchmarking {name} ---")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(WORKSPACE_ROOT)

        if fw_type == "granian":
            cmd = [
                granian_bin,
                "--interface", "asgi",
                "--host", host,
                "--port", str(port),
                "--workers", "1",
                fw["module"],
            ]
        else:
            cmd = fw["command"]

        server_proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            # Wait for readiness
            ready = wait_for_server(f"http://{host}:{port}/plaintext", timeout=10.0)
            if not ready:
                print(f"ERROR: Server {name} failed to become ready within timeout.", file=sys.stderr)
                continue

            # Warmup
            print("  Warming up (2s)...")
            try:
                subprocess.run(
                    [oha_bin, "--no-tui", "-z", "2s", "-c", "20", f"http://{host}:{port}/plaintext"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

            # Benchmark each route
            for route in ROUTES:
                url = f"http://{host}:{port}{route['path']}"
                print(f"  Benchmarking route {route['name']} ({url})...")
                res = run_oha_bench(oha_bin, url, duration_s=duration, concurrency=concurrency)
                print(f"    -> {res['rps']:,} req/s | p50: {res['p50_ms']} ms | p99: {res['p99_ms']} ms | errors: {res['errors']}")
                results.append({
                    "framework": name,
                    "route": route["name"],
                    "tool": "oha",
                    "workers": 1,
                    "rps": res["rps"],
                    "p50_ms": res["p50_ms"],
                    "p99_ms": res["p99_ms"],
                    "errors": res["errors"],
                })

        finally:
            server_proc.send_signal(signal.SIGINT)
            try:
                server_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()
            time.sleep(1.0)

    # Format Markdown Table
    md_table = []
    md_table.append("| framework | route | tool | workers | RPS | p50 ms | p99 ms | errors |")
    md_table.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for r in results:
        md_table.append(
            f"| {r['framework']} | {r['route']} | {r['tool']} | {r['workers']} | {r['rps']:,} | {r['p50_ms']} | {r['p99_ms']} | {r['errors']} |"
        )

    table_str = "\n".join(md_table)

    results_file = COMPARE_DIR / "results.md"
    results_content = f"""# Honest ASGI / Web Framework Comparison Results

Generated with `perf/compare/run.sh` on {time.strftime('%Y-%m-%d %H:%M:%S')}.
Test parameters: 1 worker process, duration 10s, concurrency 50 keep-alive connections via `oha`.

{table_str}

*Note: Benchmarks measure framework overhead on localhost. Published numbers represent honest local measurements.*
"""
    results_file.write_text(results_content)

    print("\n" + "=" * 80)
    print("  HONEST BENCHMARK COMPARISON RESULTS")
    print("=" * 80)
    print(table_str)
    print("=" * 80 + "\n")
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
