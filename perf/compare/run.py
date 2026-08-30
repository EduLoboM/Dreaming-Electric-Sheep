#!/usr/bin/env python3
"""
Localhost ASGI / Rust runtime framework benchmark runner.
Measures framework overhead and server ceilings with shared in-memory fixtures.
(Not the TechEmpower Framework Benchmarks. No Postgres.)

Runs two distinct comparison suites:
1. Ceiling Comparison (apples-to-apples msgspec encoder: DES vs Granian Raw vs Uvicorn Raw)
2. Default Stack Comparison (stock helpers out of the box: DES vs Emmett vs Sanic vs Robyn vs Litestar vs FastAPI)

Runs N iterations per route, takes the median, and records exact server runtimes and system info.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
COMPARE_DIR = Path(__file__).resolve().parent

CEILING_FRAMEWORKS = [
    {
        "id": "granian_raw_rsgi",
        "name": "Granian (Raw RSGI)",
        "runtime": "Granian (Raw RSGI, 1 worker, msgspec)",
        "type": "granian_rsgi",
        "module": "perf.compare.granian_raw_rsgi_app:app",
    },
    {
        "id": "granian_raw_asgi",
        "name": "Granian (Raw ASGI)",
        "runtime": "Granian (Raw ASGI, 1 worker, msgspec)",
        "type": "granian",
        "module": "perf.compare.granian_raw_app:app",
    },
    {
        "id": "des_ceiling_rsgi",
        "name": "Dreaming Electric Sheep (RSGI)",
        "runtime": "Granian (RSGI, 1 worker, msgspec)",
        "type": "granian_rsgi",
        "module": "perf.compare.des_ceiling_app:app",
    },
    {
        "id": "des_ceiling_asgi",
        "name": "Dreaming Electric Sheep (ASGI)",
        "runtime": "Granian (ASGI, 1 worker, msgspec)",
        "type": "granian",
        "module": "perf.compare.des_ceiling_app:app",
    },
    {
        "id": "uvicorn_raw",
        "name": "Uvicorn (Raw ASGI)",
        "runtime": "Uvicorn (Raw ASGI, 1 worker, msgspec)",
        "type": "uvicorn",
        "module": "perf.compare.uvicorn_raw_app:app",
    },
]

DEFAULT_STACK_FRAMEWORKS = [
    {
        "id": "des_rsgi",
        "name": "Dreaming Electric Sheep (RSGI)",
        "runtime": "Granian (RSGI, 1 worker, stock helpers)",
        "type": "granian_rsgi",
        "module": "perf.compare.des_app:app",
    },
    {
        "id": "des_asgi",
        "name": "Dreaming Electric Sheep (ASGI)",
        "runtime": "Granian (ASGI, 1 worker, stock helpers)",
        "type": "granian",
        "module": "perf.compare.des_app:app",
    },
    {
        "id": "emmett",
        "name": "Emmett",
        "runtime": "Granian (RSGI/ASGI, 1 worker)",
        "type": "granian",
        "module": "perf.compare.emmett_app:app",
    },
    {
        "id": "sanic",
        "name": "Sanic",
        "runtime": "Sanic (1 worker)",
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
    },
    {
        "id": "robyn",
        "name": "Robyn",
        "runtime": "Robyn Rust (1 worker process)",
        "type": "standalone",
        "command": [
            sys.executable,
            str(COMPARE_DIR / "robyn_app.py"),
            "--port", "{port}",
            "--processes", "1",
            "--workers", "1",
            "--log-level", "WARN",
            "--disable-openapi",
        ],
    },
    {
        "id": "litestar",
        "name": "Litestar",
        "runtime": "Granian (ASGI, 1 worker)",
        "type": "granian",
        "module": "perf.compare.litestar_app:app",
    },
    {
        "id": "fastapi",
        "name": "FastAPI",
        "runtime": "Granian (ASGI, 1 worker)",
        "type": "granian",
        "module": "perf.compare.fastapi_app:app",
    },
    {
        "id": "flask",
        "name": "Flask",
        "runtime": "Granian (WSGI, 1 worker)",
        "type": "granian_wsgi",
        "module": "perf.compare.flask_app:app",
    },
    {
        "id": "django",
        "name": "Django",
        "runtime": "Granian (WSGI, 1 worker, stripped middleware)",
        "type": "granian_wsgi",
        "module": "perf.compare.django_app:app",
    },
]

RSGI_FRAMEWORKS = [
    {
        "id": "des_rsgi",
        "name": "Dreaming Electric Sheep (RSGI)",
        "runtime": "Granian (RSGI, 1 worker, stock helpers)",
        "type": "granian_rsgi",
        "module": "perf.compare.des_app:app",
    },
    {
        "id": "des_asgi",
        "name": "Dreaming Electric Sheep (ASGI)",
        "runtime": "Granian (ASGI, 1 worker, stock helpers)",
        "type": "granian",
        "module": "perf.compare.des_app:app",
    },
    {
        "id": "granian_raw",
        "name": "Granian (Raw ASGI)",
        "runtime": "Granian (Raw ASGI, 1 worker, msgspec)",
        "type": "granian",
        "module": "perf.compare.granian_raw_app:app",
    },
]

ROUTES = [
    {"id": "plaintext", "name": "Plaintext", "path": "/plaintext"},
    {"id": "json", "name": "JSON", "path": "/json"},
    {"id": "db", "name": "Mem get", "path": "/db"},
    {"id": "queries", "name": "Mem get ×20", "path": "/queries?queries=20"},
    {"id": "fortunes", "name": "HTML fortunes (in-memory)", "path": "/fortunes"},
    {"id": "updates", "name": "Mem update ×20", "path": "/updates?queries=20"},
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


def wait_for_port_free(host: str, port: int, timeout: float = 6.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return True
            except OSError:
                time.sleep(0.1)
    return False


def wait_for_server(url: str, timeout: float = 12.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False


def run_single_oha_run(
    oha_bin: str,
    url: str,
    duration_s: int = 5,
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

    return {
        "rps": rps,
        "p50_ms": lat_p50_s * 1000.0,
        "p99_ms": lat_p99_s * 1000.0,
        "errors": error_count,
    }


def benchmark_route_median(
    oha_bin: str,
    url: str,
    duration_s: int = 5,
    concurrency: int = 50,
    num_runs: int = 3,
) -> Dict[str, Any]:
    rps_list: List[float] = []
    p50_list: List[float] = []
    p99_list: List[float] = []
    total_errors = 0

    for i in range(num_runs):
        print(f"    [Run {i+1}/{num_runs}] measuring {duration_s}s at -c {concurrency}...", end="", flush=True)
        res = run_single_oha_run(oha_bin, url, duration_s=duration_s, concurrency=concurrency)
        rps_list.append(res["rps"])
        p50_list.append(res["p50_ms"])
        p99_list.append(res["p99_ms"])
        total_errors += res["errors"]
        print(f" -> {res['rps']:,.1f} req/s (p50: {res['p50_ms']:.2f}ms, p99: {res['p99_ms']:.2f}ms)")
        if i < num_runs - 1:
            time.sleep(0.5)

    med_rps = statistics.median(rps_list)
    med_p50 = statistics.median(p50_list)
    med_p99 = statistics.median(p99_list)

    return {
        "rps": round(med_rps, 2),
        "p50_ms": round(med_p50, 3),
        "p99_ms": round(med_p99, 3),
        "errors": total_errors,
        "runs": num_runs,
    }


def get_system_info(oha_bin: str) -> Dict[str, str]:
    def get_pkg_ver(pkg: str) -> str:
        try:
            return importlib.metadata.version(pkg)
        except Exception:
            return "unknown"

    oha_ver = "oha"
    try:
        proc = subprocess.run([oha_bin, "--version"], stdout=subprocess.PIPE, text=True)
        oha_ver = proc.stdout.strip()
    except Exception:
        pass

    simd_isa = "SCALAR"
    try:
        from dreaming_electric_sheep import _des_core
        simd_isa = _des_core.get_simd_isa_info()
    except Exception:
        pass

    return {
        "python": sys.version.split()[0],
        "os": platform.platform(),
        "arch": platform.machine(),
        "simd_isa": simd_isa,
        "granian": get_pkg_ver("granian"),
        "uvicorn": get_pkg_ver("uvicorn"),
        "emmett": get_pkg_ver("emmett"),
        "sanic": get_pkg_ver("sanic"),
        "robyn": get_pkg_ver("robyn"),
        "litestar": get_pkg_ver("litestar"),
        "fastapi": get_pkg_ver("fastapi"),
        "flask": get_pkg_ver("flask"),
        "django": get_pkg_ver("django"),
        "oha": oha_ver,
    }


def run_framework_benchmarks(
    frameworks: List[Dict[str, Any]],
    routes: List[Dict[str, Any]],
    oha_bin: str,
    granian_bin: str,
    uvicorn_bin: str,
    host: str,
    port: int,
    duration: int,
    concurrency: int,
    num_runs: int,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for fw in frameworks:
        name = fw["name"]
        runtime = fw["runtime"]
        fw_type = fw["type"]
        print(f"\n--- Benchmarking {name} ({runtime}) ---")

        wait_for_port_free(host, port, timeout=6.0)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(WORKSPACE_ROOT)
        for k in list(env.keys()):
            if k.startswith("APP_"):
                del env[k]

        if fw_type == "granian_rsgi":
            cmd = [
                granian_bin,
                "--interface", "rsgi",
                "--host", host,
                "--port", str(port),
                "--workers", "1",
                fw["module"],
            ]
        elif fw_type == "granian":
            cmd = [
                granian_bin,
                "--interface", "asgi",
                "--host", host,
                "--port", str(port),
                "--workers", "1",
                fw["module"],
            ]
        elif fw_type == "uvicorn":
            cmd = [
                uvicorn_bin,
                fw["module"],
                "--host", host,
                "--port", str(port),
                "--workers", "1",
                "--no-access-log",
            ]
        elif fw_type in ("sanic", "standalone"):
            cmd = [arg.format(port=port) for arg in fw["command"]]

        server_proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ready = wait_for_server(f"http://{host}:{port}/plaintext", timeout=12.0)
            if not ready:
                print(f"ERROR: Server {name} failed to become ready within timeout.", file=sys.stderr)
                continue

            print("  Warming up (2s)...")
            try:
                subprocess.run(
                    [oha_bin, "--no-tui", "-z", "2s", "-c", "20", f"http://{host}:{port}/plaintext"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

            for route in routes:
                url = f"http://{host}:{port}{route['path']}"
                print(f"  Measuring {route['name']} ({url}):")
                res = benchmark_route_median(oha_bin, url, duration_s=duration, concurrency=concurrency, num_runs=num_runs)
                print(f"  ==> Median: {res['rps']:,} req/s | p50: {res['p50_ms']} ms | p99: {res['p99_ms']} ms | total errors: {res['errors']}")
                results.append({
                    "framework": name,
                    "runtime": runtime,
                    "route": route["name"],
                    "tool": "oha",
                    "rps": res["rps"],
                    "p50_ms": res["p50_ms"],
                    "p99_ms": res["p99_ms"],
                    "errors": res["errors"],
                })

        finally:
            server_proc.send_signal(signal.SIGINT)
            try:
                server_proc.wait(timeout=4.0)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()
            time.sleep(1.0)
            wait_for_port_free(host, port, timeout=6.0)

    return results


def format_table(results: List[Dict[str, Any]]) -> str:
    md = []
    md.append("| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        md.append(
            f"| {r['framework']} | {r['route']} | {r['runtime']} | {r['tool']} | {r['rps']:,} | {r['p50_ms']} | {r['p99_ms']} | {r['errors']} |"
        )
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Localhost framework overhead runner with shared in-memory fixtures (Not TechEmpower. No Postgres).")
    parser.add_argument("--duration", "-z", type=int, default=5, help="Duration in seconds per run (default: 5)")
    parser.add_argument("--concurrency", "-c", type=int, default=50, help="Concurrency / keep-alive connections (default: 50)")
    parser.add_argument("--runs", "-n", type=int, default=3, help="Number of runs per test to compute median (default: 3)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind servers (default: 8000)")
    parser.add_argument("--mode", type=str, default="all", choices=["all", "ceiling", "default", "rsgi"], help="Comparison mode to run (default: all)")
    args = parser.parse_args()

    oha_bin = find_oha()
    venv_bin = Path(sys.executable).parent
    granian_bin = shutil.which("granian") or str(venv_bin / "granian")
    uvicorn_bin = shutil.which("uvicorn") or str(venv_bin / "uvicorn")

    port = args.port
    host = "127.0.0.1"
    duration = args.duration
    concurrency = args.concurrency
    num_runs = args.runs

    sys_info = get_system_info(oha_bin)

    print(f"\n{'=' * 90}")
    print(f"  FRAMEWORK OVERHEAD BENCHMARK SUITE ({sys_info['oha']})")
    print(f"  (Localhost framework overhead + shared in-memory fixture. Not TechEmpower. No Postgres.)")
    print(f"  Settings: {num_runs} runs of {duration}s each per route | Concurrency: {concurrency} | Aggregation: Median")
    print(f"{'=' * 90}\n")

    ceiling_results: List[Dict[str, Any]] = []
    default_results: List[Dict[str, Any]] = []
    rsgi_results: List[Dict[str, Any]] = []

    if args.mode in ("all", "ceiling"):
        print("\n==========================================================================================")
        print("  MODE A: CEILING COMPARISON (Apples-to-Apples msgspec Encoder)")
        print("  DES vs Granian Raw vs Uvicorn Raw (all encode per request with msgspec)")
        print("==========================================================================================")
        ceiling_results = run_framework_benchmarks(
            CEILING_FRAMEWORKS, ROUTES, oha_bin, granian_bin, uvicorn_bin, host, port, duration, concurrency, num_runs
        )

    if args.mode in ("all", "default"):
        print("\n==========================================================================================")
        print("  MODE B: DEFAULT STACK COMPARISON (Stock Helpers Out-of-the-Box)")
        print("  DES vs Emmett vs Sanic vs Robyn vs Litestar vs FastAPI (framework default helpers)")
        print("==========================================================================================")
        default_results = run_framework_benchmarks(
            DEFAULT_STACK_FRAMEWORKS, ROUTES, oha_bin, granian_bin, uvicorn_bin, host, port, duration, concurrency, num_runs
        )

    if args.mode == "rsgi":
        print("\n==========================================================================================")
        print("  MODE C: PROTOCOL COMPARISON (RSGI vs ASGI vs Raw)")
        print("  DES RSGI vs DES ASGI vs Granian Raw ASGI")
        print("==========================================================================================")
        rsgi_results = run_framework_benchmarks(
            RSGI_FRAMEWORKS, ROUTES, oha_bin, granian_bin, uvicorn_bin, host, port, duration, concurrency, num_runs
        )

    # Build results.md
    results_file = COMPARE_DIR / "results.md"
    content_parts = [
        "# ASGI / Rust Runtime Framework Benchmark Results",
        "",
        f"Generated with `perf/compare/run.sh` on {time.strftime('%Y-%m-%d %H:%M:%S')}.",
        f"Test parameters: {num_runs} runs of {duration}s per route (median reported), concurrency {concurrency} keep-alive connections via `oha` on localhost.",
        "",
        "*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*",
        "",
    ]

    # If running only rsgi mode, parse existing Table A and Table B from results.md if available
    if args.mode == "rsgi" and results_file.exists():
        existing_text = results_file.read_text(encoding="utf8")
        if "## Table A: Ceiling Comparison" in existing_text:
            part_a = existing_text.split("## Table A: Ceiling Comparison")[1].split("## Table")[0].strip()
            content_parts.extend([
                "## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)",
                part_a,
                "",
            ])
        if "## Table B: Default Stack Comparison" in existing_text:
            part_b = existing_text.split("## Table B: Default Stack Comparison")[1].split("## Table")[0].split("### Environment")[0].strip()
            content_parts.extend([
                "## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)",
                part_b,
                "",
            ])
    else:
        if ceiling_results:
            content_parts.extend([
                "## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)",
                "Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.",
                "",
                format_table(ceiling_results),
                "",
            ])

        if default_results:
            content_parts.extend([
                "## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)",
                "Measures out-of-the-box performance using each framework's stock response/serialization helpers.",
                "",
                format_table(default_results),
                "",
            ])

    if rsgi_results:
        content_parts.extend([
            "## Table C: Protocol Comparison (RSGI vs ASGI vs Raw)",
            "Measures the overhead difference between Granian RSGI, Granian ASGI, and Raw Granian ASGI.",
            "",
            format_table(rsgi_results),
            "",
        ])

    content_parts.extend([
        "### Environment & System Specifications",
        f"- Python: {sys_info['python']} (CPython)",
        f"- OS / Platform: {sys_info['os']} ({sys_info['arch']})",
        f"- SIMD ISA: {sys_info['simd_isa']}",
        "- Runtimes & Frameworks:",
        f"  - Granian: `{sys_info['granian']}`",
        f"  - Uvicorn: `{sys_info['uvicorn']}`",
        f"  - Emmett: `{sys_info['emmett']}`",
        f"  - Sanic: `{sys_info['sanic']}`",
        f"  - Robyn: `{sys_info['robyn']}`",
        f"  - Litestar: `{sys_info['litestar']}`",
        f"  - FastAPI: `{sys_info['fastapi']}`",
        f"  - Flask: `{sys_info['flask']}`",
        f"  - Django: `{sys_info['django']}`",
        f"- Load Generator: {sys_info['oha']}",
        "",
    ])

    results_content = "\n".join(content_parts)
    results_file.write_text(results_content)

    print("\n" + "=" * 90)
    print("  BENCHMARK COMPLETE - RESULTS SAVED")
    print("=" * 90)
    print(f"Results saved to: {results_file}\n")


if __name__ == "__main__":
    main()
