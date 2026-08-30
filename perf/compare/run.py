#!/usr/bin/env python3
"""
Honest ASGI / Rust runtime framework benchmark runner for:
Dreaming Electric Sheep vs Robyn vs Litestar vs FastAPI.
Runs 3 iterations per route, takes the median, and records exact server runtimes and system info.
"""
import sys
import os
import time
import json
import shutil
import signal
import platform
import statistics
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
COMPARE_DIR = Path(__file__).resolve().parent

FRAMEWORKS = [
    {
        "name": "Dreaming Electric Sheep",
        "runtime": "Granian (ASGI, 1 worker)",
        "type": "granian",
        "module": "perf.compare.des_app:app",
    },
    {
        "name": "Robyn",
        "runtime": "Robyn Rust (1 worker process)",
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
        "runtime": "Granian (ASGI, 1 worker)",
        "type": "granian",
        "module": "perf.compare.litestar_app:app",
    },
    {
        "name": "FastAPI",
        "runtime": "Granian (ASGI, 1 worker)",
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


def run_single_oha_run(
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

    return {
        "rps": rps,
        "p50_ms": lat_p50_s * 1000.0,
        "p99_ms": lat_p99_s * 1000.0,
        "errors": error_count,
    }


def benchmark_route_median(
    oha_bin: str,
    url: str,
    duration_s: int = 10,
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
            time.sleep(1.0)

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
    import importlib.metadata
    
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
        "robyn": get_pkg_ver("robyn"),
        "litestar": get_pkg_ver("litestar"),
        "fastapi": get_pkg_ver("fastapi"),
        "oha": oha_ver,
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
    num_runs = 3

    sys_info = get_system_info(oha_bin)
    results: List[Dict[str, Any]] = []

    print(f"Starting comparison benchmarks using {sys_info['oha']}...")
    print(f"Settings: {num_runs} runs of {duration}s each per route | Concurrency: {concurrency} | Aggregation: Median\n")

    for fw in FRAMEWORKS:
        name = fw["name"]
        runtime = fw["runtime"]
        fw_type = fw["type"]
        print(f"--- Benchmarking {name} ({runtime}) ---")

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
            ready = wait_for_server(f"http://{host}:{port}/plaintext", timeout=10.0)
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

            for route in ROUTES:
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
                server_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()
            time.sleep(1.0)

    # Format Markdown Table
    md_table = []
    md_table.append("| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |")
    md_table.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for r in results:
        md_table.append(
            f"| {r['framework']} | {r['route']} | {r['runtime']} | {r['tool']} | {r['rps']:,} | {r['p50_ms']} | {r['p99_ms']} | {r['errors']} |"
        )

    table_str = "\n".join(md_table)

    results_file = COMPARE_DIR / "results.md"
    results_content = f"""# Honest ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on {time.strftime('%Y-%m-%d %H:%M:%S')}.
Test parameters: 3 runs of 10s per route (median reported), concurrency 50 keep-alive connections via `oha`.

{table_str}

### Environment & System Specifications
- **Python**: {sys_info['python']} (CPython)
- **OS / Platform**: {sys_info['os']} ({sys_info['arch']})
- **Active SIMD ISA**: {sys_info['simd_isa']}
- **Granian**: {sys_info['granian']} | **Robyn**: {sys_info['robyn']} | **Litestar**: {sys_info['litestar']} | **FastAPI**: {sys_info['fastapi']}
- **Load Generator**: {sys_info['oha']}

*Note: Dreaming Electric Sheep, Litestar, and FastAPI execute as ASGI applications under Granian (1 worker). Robyn executes under its standalone native Rust server runtime (1 process, 1 worker). Benchmarks measure framework + server overhead on localhost.*
"""
    results_file.write_text(results_content)

    print("\n" + "=" * 90)
    print("  HONEST BENCHMARK COMPARISON RESULTS (3-RUN MEDIAN)")
    print("=" * 90)
    print(table_str)
    print("=" * 90 + "\n")
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
