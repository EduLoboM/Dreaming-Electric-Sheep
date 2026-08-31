# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-31 17:55:43.
Test parameters: 5 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 101,573.42 | 0.47 | 0.846 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 96,725.28 | 0.479 | 0.902 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 97,370.14 | 0.467 | 0.983 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 51,697.68 | 0.948 | 1.642 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 25,862.2 | 1.791 | 4.022 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 36,320.9 | 1.317 | 2.552 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 70,343.07 | 0.699 | 1.364 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 72,068.69 | 0.633 | 1.325 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 66,651.79 | 0.669 | 1.474 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 40,248.96 | 1.179 | 2.477 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 22,480.18 | 2.073 | 4.518 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 32,424.9 | 1.464 | 2.932 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 77,479.26 | 0.575 | 1.545 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 71,685.83 | 0.605 | 1.795 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 69,456.09 | 0.636 | 1.859 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 37,367.75 | 1.28 | 2.679 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 26,411.26 | 1.84 | 3.349 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 33,479.1 | 1.443 | 2.576 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 73,347.98 | 0.608 | 1.718 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 66,781.43 | 0.667 | 1.827 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 64,345.42 | 0.703 | 1.941 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 28,634.86 | 1.564 | 4.219 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 20,869.36 | 2.242 | 5.222 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 25,841.31 | 1.825 | 4.185 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 45,141.17 | 1.028 | 2.208 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 44,845.85 | 1.012 | 2.37 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 39,479.55 | 1.188 | 2.634 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 27,776.18 | 1.649 | 3.745 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 18,013.58 | 2.558 | 6.556 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 23,548.14 | 1.953 | 4.349 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 54,610.44 | 0.719 | 2.238 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 58,617.54 | 0.712 | 2.078 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 62,643.37 | 0.676 | 2.108 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 33,968.6 | 1.354 | 3.565 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 26,208.06 | 1.845 | 3.246 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 27,064.48 | 1.69 | 4.352 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 53,654.49 | 0.822 | 2.057 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 56,336.6 | 0.778 | 2.052 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 56,362.63 | 0.766 | 2.192 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 31,565.85 | 1.471 | 3.424 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 23,948.64 | 2.011 | 3.768 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 28,435.18 | 1.677 | 3.297 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 47,619.23 | 0.987 | 2.54 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 36,772.32 | 1.212 | 3.526 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 41,197.44 | 1.134 | 2.921 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 23,385.5 | 2.037 | 3.939 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 20,619.62 | 2.311 | 4.282 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 19,202.82 | 2.475 | 4.498 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 37,436.67 | 1.237 | 2.727 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 34,246.25 | 1.343 | 2.876 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 31,727.28 | 1.411 | 3.239 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 19,446.25 | 2.343 | 5.021 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 16,008.46 | 2.992 | 6.589 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 16,405.36 | 2.866 | 6.163 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 22,838.76 | 2.081 | 4.704 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 23,090.31 | 2.195 | 4.136 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 21,441.45 | 2.333 | 4.618 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 9,783.07 | 4.913 | 10.742 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 11,640.49 | 4.228 | 8.808 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 13,419.87 | 3.858 | 6.64 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 28,096.24 | 1.712 | 3.261 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 23,168.58 | 1.988 | 4.887 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 26,139.98 | 1.859 | 3.442 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 14,544.22 | 3.296 | 5.814 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 14,456.77 | 3.339 | 5.236 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 14,311.9 | 3.318 | 5.839 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 15,421.06 | 2.998 | 6.653 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 16,053.03 | 2.97 | 5.059 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 13,352.51 | 3.471 | 6.606 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 5,718.55 | 8.576 | 11.49 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 10,738.82 | 4.5 | 6.821 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 5,745.86 | 8.533 | 11.054 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 19,936.06 | 2.392 | 4.24 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 17,730.4 | 2.724 | 4.188 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 16,301.05 | 2.97 | 4.26 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 5,395.47 | 8.825 | 13.239 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 9,890.72 | 4.871 | 8.645 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 4,968.91 | 9.571 | 17.566 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 16,498.24 | 2.828 | 7.36 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 11,314.15 | 3.897 | 9.23 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 12,482.07 | 3.807 | 6.751 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 5,689.64 | 8.613 | 11.721 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 10,493.39 | 4.611 | 8.546 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 5,407.22 | 9.098 | 11.818 | 0 |

### Environment & System Specifications
- Python: 3.14.7 (CPython)
- OS / Platform: Linux-7.2.2-1-cachyos-x86_64-with-glibc2.44 (x86_64)
- SIMD ISA: AVX2
- Runtimes & Frameworks:
  - Granian: `2.8.2`
  - Uvicorn: `0.34.2`
  - Emmett: `2.8.1`
  - Sanic: `25.12.1`
  - Robyn: `0.88.0`
  - Litestar: `2.24.0`
  - FastAPI: `0.141.1`
  - Flask: `3.1.1`
  - Django: `6.1`
- Load Generator: oha 1.16.0
