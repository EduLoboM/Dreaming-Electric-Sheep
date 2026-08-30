# Honest ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-30 12:16:48.
Test parameters: 3 runs of 10s per route (median reported), concurrency 50 keep-alive connections via `oha`.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep | plaintext | Granian (ASGI, 1 worker) | oha | 27,971.07 | 1.527 | 4.593 | 0 |
| Dreaming Electric Sheep | json | Granian (ASGI, 1 worker) | oha | 20,931.71 | 1.91 | 5.91 | 0 |
| Robyn | plaintext | Robyn Rust (1 worker process) | oha | 10,453.47 | 4.386 | 12.147 | 0 |
| Robyn | json | Robyn Rust (1 worker process) | oha | 9,714.83 | 4.835 | 14.458 | 0 |
| Litestar | plaintext | Granian (ASGI, 1 worker) | oha | 13,048.45 | 3.447 | 9.451 | 0 |
| Litestar | json | Granian (ASGI, 1 worker) | oha | 13,639.51 | 3.412 | 7.398 | 0 |
| FastAPI | plaintext | Granian (ASGI, 1 worker) | oha | 10,203.49 | 4.621 | 10.979 | 0 |
| FastAPI | json | Granian (ASGI, 1 worker) | oha | 8,351.62 | 5.587 | 14.257 | 0 |

### Environment & System Specifications
- **Python**: 3.14.7 (CPython)
- **OS / Platform**: Linux-7.2.2-1-cachyos-x86_64-with-glibc2.44 (x86_64)
- **Active SIMD ISA**: AVX2
- **Granian**: 2.8.2 | **Robyn**: 0.88.0 | **Litestar**: 2.24.0 | **FastAPI**: 0.141.1
- **Load Generator**: oha 1.16.0

*Note: Dreaming Electric Sheep, Litestar, and FastAPI execute as ASGI applications under Granian (1 worker). Robyn executes under its standalone native Rust server runtime (1 process, 1 worker). Benchmarks measure framework + server overhead on localhost.*
