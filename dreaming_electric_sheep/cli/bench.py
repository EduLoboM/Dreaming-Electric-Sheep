"""
High-performance in-tree benchmark tool (`des bench`).
"""
import sys
import time
import asyncio
import shutil
import subprocess
from typing import Dict, Any, List


async def _run_async_bench(url: str, duration: int = 5, concurrency: int = 50) -> Dict[str, Any]:
    try:
        import httpx
    except ImportError:
        import urllib.request
        httpx = None

    latencies: List[float] = []
    total_requests = 0
    errors = 0
    stop_event = asyncio.Event()

    async def worker():
        nonlocal total_requests, errors
        if httpx:
            async with httpx.AsyncClient(timeout=10.0) as client:
                while not stop_event.is_set():
                    t0 = time.perf_counter()
                    try:
                        res = await client.get(url)
                        if res.status_code < 400:
                            latencies.append((time.perf_counter() - t0) * 1000.0)
                            total_requests += 1
                        else:
                            errors += 1
                    except Exception:
                        errors += 1
        else:
            loop = asyncio.get_running_loop()
            while not stop_event.is_set():
                t0 = time.perf_counter()
                try:
                    def req():
                        with urllib.request.urlopen(url) as res:
                            return res.status
                    status = await loop.run_in_executor(None, req)
                    if status < 400:
                        latencies.append((time.perf_counter() - t0) * 1000.0)
                        total_requests += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1

    t_start = time.perf_counter()
    tasks = [asyncio.create_task(worker()) for _ in range(concurrency)]
    await asyncio.sleep(duration)
    stop_event.set()
    await asyncio.gather(*tasks, return_exceptions=True)
    actual_duration = time.perf_counter() - t_start

    latencies.sort()
    rps = total_requests / actual_duration if actual_duration > 0 else 0
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0

    return {
        "url": url,
        "duration_seconds": round(actual_duration, 2),
        "concurrency": concurrency,
        "total_requests": total_requests,
        "errors": errors,
        "requests_per_second": round(rps, 2),
        "latency_p50_ms": round(p50, 3),
        "latency_p95_ms": round(p95, 3),
        "latency_p99_ms": round(p99, 3),
    }


def run_benchmark(url: str = "http://127.0.0.1:8000/", duration: int = 5, concurrency: int = 50):
    # Check for external tools first (oha / wrk)
    if shutil.which("oha"):
        print(f"Running oha benchmark on {url} (concurrency: {concurrency}, duration: {duration}s)...")
        subprocess.run(["oha", "-z", f"{duration}s", "-c", str(concurrency), url])
        return
    elif shutil.which("wrk"):
        print(f"Running wrk benchmark on {url} (threads: 4, connections: {concurrency}, duration: {duration}s)...")
        subprocess.run(["wrk", "-t", "4", "-c", str(concurrency), "-d", f"{duration}s", url])
        return

    print(f"Running in-tree async load test on {url} (concurrency: {concurrency}, duration: {duration}s)...")
    res = asyncio.run(_run_async_bench(url, duration=duration, concurrency=concurrency))
    
    print("\n" + "=" * 50)
    print("  📊 BENCHMARK RESULTS")
    print("=" * 50)
    print(f"  Target URL:        {res['url']}")
    print(f"  Duration:          {res['duration_seconds']}s")
    print(f"  Concurrency:       {res['concurrency']}")
    print(f"  Total Completed:   {res['total_requests']}")
    print(f"  Total Errors:      {res['errors']}")
    print(f"  Throughput:        🚀 {res['requests_per_second']} req/s")
    print(f"  Latency p50:       {res['latency_p50_ms']} ms")
    print(f"  Latency p95:       {res['latency_p95_ms']} ms")
    print(f"  Latency p99:       {res['latency_p99_ms']} ms")
    print("=" * 50 + "\n")
