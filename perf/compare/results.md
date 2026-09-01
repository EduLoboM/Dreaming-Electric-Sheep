# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-09-01 11:43:36.
Test parameters: 5 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 130,147.85 | 0.357 | 0.658 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 132,491.02 | 0.349 | 0.62 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 129,247.23 | 0.351 | 0.701 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 61,794.18 | 0.783 | 1.361 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 36,078.13 | 1.352 | 2.187 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 49,109.38 | 0.988 | 1.518 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 95,698.96 | 0.476 | 0.946 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 93,921.51 | 0.457 | 1.008 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 92,681.8 | 0.455 | 1.072 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 50,458.91 | 0.97 | 1.822 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 32,137.83 | 1.531 | 2.402 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 42,186.44 | 1.157 | 1.971 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 128,941.58 | 0.35 | 0.784 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 123,586.4 | 0.362 | 0.882 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 121,578.26 | 0.372 | 0.954 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 59,000.52 | 0.813 | 1.574 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 32,782.5 | 1.467 | 2.464 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 47,596.71 | 1.015 | 1.506 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 88,623.0 | 0.491 | 1.298 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 88,529.56 | 0.502 | 1.33 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 80,684.59 | 0.55 | 1.51 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 46,522.42 | 1.037 | 2.092 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 29,072.75 | 1.671 | 2.882 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 38,879.8 | 1.251 | 2.213 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 55,480.86 | 0.818 | 1.733 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 53,698.38 | 0.849 | 1.788 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 51,735.37 | 0.887 | 1.868 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 35,765.2 | 1.336 | 2.663 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 26,126.81 | 1.855 | 3.643 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 31,759.22 | 1.527 | 3.026 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 121,068.57 | 0.371 | 0.92 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 122,107.11 | 0.371 | 0.924 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 118,082.89 | 0.383 | 1.0 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 56,176.1 | 0.853 | 1.518 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 32,432.01 | 1.491 | 2.137 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 45,328.04 | 1.073 | 1.555 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 86,349.7 | 0.502 | 1.379 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 86,743.94 | 0.512 | 1.355 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 79,035.02 | 0.555 | 1.518 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 40,206.2 | 1.137 | 2.637 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 25,639.25 | 1.743 | 3.791 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 39,074.5 | 1.248 | 2.25 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 57,930.32 | 0.829 | 1.855 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 52,004.0 | 0.929 | 2.1 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 50,008.16 | 0.971 | 2.033 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 24,395.57 | 1.926 | 3.722 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 22,378.26 | 2.143 | 3.762 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 21,441.07 | 2.238 | 3.842 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 46,014.08 | 1.014 | 2.001 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 42,729.13 | 1.109 | 2.17 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 40,802.34 | 1.164 | 2.286 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 24,765.76 | 1.916 | 3.892 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 21,945.8 | 2.101 | 3.99 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 22,895.75 | 2.011 | 4.068 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 30,884.84 | 1.687 | 2.65 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 28,311.13 | 1.826 | 3.072 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 27,791.36 | 1.873 | 3.106 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 18,921.05 | 2.785 | 4.456 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 17,786.27 | 2.977 | 4.953 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 17,727.45 | 2.957 | 4.843 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 33,523.27 | 1.471 | 2.06 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 32,140.37 | 1.528 | 2.799 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 30,722.2 | 1.6 | 2.545 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 20,599.72 | 2.393 | 3.841 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 16,694.59 | 2.954 | 3.924 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 18,930.04 | 2.614 | 3.491 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 24,231.09 | 2.033 | 2.584 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 20,367.31 | 2.429 | 3.123 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 19,050.19 | 2.597 | 3.49 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 7,388.86 | 6.71 | 8.599 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 13,517.67 | 3.656 | 5.094 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 6,857.83 | 7.183 | 9.188 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 23,793.94 | 2.071 | 3.209 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 20,186.44 | 2.444 | 3.659 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 18,644.19 | 2.657 | 3.321 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 7,270.6 | 6.813 | 8.577 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 13,273.95 | 3.744 | 4.783 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 6,985.59 | 7.091 | 8.534 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 24,017.54 | 2.053 | 2.927 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 20,237.55 | 2.451 | 3.196 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 18,763.47 | 2.63 | 4.064 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,281.3 | 6.816 | 8.505 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 13,455.88 | 3.692 | 4.455 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,011.47 | 7.08 | 8.965 | 0 |

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
