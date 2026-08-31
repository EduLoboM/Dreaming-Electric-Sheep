# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-31 13:30:28.
Test parameters: 5 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 183,557.36 | 0.261 | 0.438 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 144,815.05 | 0.322 | 0.56 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 146,836.94 | 0.311 | 0.617 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 74,404.45 | 0.664 | 1.007 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 43,639.25 | 1.141 | 1.412 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 60,261.7 | 0.829 | 1.054 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 117,157.6 | 0.371 | 0.789 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 115,133.64 | 0.355 | 0.846 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 114,108.1 | 0.362 | 0.924 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 62,341.95 | 0.781 | 1.583 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 39,030.74 | 1.266 | 1.757 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 51,393.35 | 0.96 | 1.709 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 126,680.59 | 0.363 | 1.007 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 122,479.93 | 0.38 | 1.062 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 111,741.49 | 0.418 | 1.169 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 57,396.38 | 0.869 | 1.101 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 38,682.36 | 1.283 | 1.625 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 47,967.61 | 1.035 | 1.365 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 102,120.72 | 0.436 | 1.244 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 100,048.47 | 0.45 | 1.288 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 95,955.78 | 0.482 | 1.368 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 50,587.09 | 0.969 | 1.817 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 35,781.4 | 1.39 | 1.945 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 42,548.02 | 1.163 | 1.845 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 66,784.18 | 0.718 | 1.451 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 67,645.66 | 0.709 | 1.438 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 65,406.02 | 0.728 | 1.485 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 43,117.9 | 1.105 | 2.229 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 30,661.01 | 1.56 | 3.067 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 37,882.43 | 1.274 | 2.515 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 122,827.02 | 0.374 | 1.05 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 122,801.06 | 0.38 | 1.07 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 113,811.63 | 0.414 | 1.12 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 58,351.68 | 0.851 | 1.119 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 39,370.96 | 1.266 | 1.514 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 46,949.48 | 1.043 | 1.808 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 101,789.17 | 0.442 | 1.252 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 100,209.58 | 0.453 | 1.273 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 96,535.93 | 0.484 | 1.339 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 51,355.47 | 0.957 | 1.788 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 36,029.99 | 1.382 | 2.41 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 44,383.01 | 1.119 | 1.595 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 73,600.67 | 0.651 | 1.64 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 67,086.55 | 0.721 | 1.641 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 64,461.84 | 0.751 | 1.664 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 34,394.79 | 1.451 | 1.791 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 31,156.82 | 1.597 | 2.409 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 30,484.85 | 1.642 | 2.245 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 53,754.9 | 0.863 | 1.739 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 48,822.34 | 0.958 | 1.869 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 47,146.36 | 1.003 | 2.01 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 27,552.77 | 1.763 | 3.469 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 24,247.16 | 1.993 | 3.896 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 25,321.05 | 1.931 | 3.779 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 37,027.53 | 1.429 | 2.376 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 34,183.93 | 1.568 | 2.476 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 32,937.77 | 1.608 | 2.698 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 22,648.63 | 2.372 | 3.681 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 20,986.55 | 2.576 | 3.909 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 21,004.02 | 2.56 | 3.95 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 41,183.37 | 1.205 | 1.791 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 39,855.07 | 1.25 | 1.847 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 37,963.45 | 1.31 | 1.713 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 25,535.96 | 1.959 | 2.28 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 20,518.83 | 2.429 | 3.314 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 23,323.7 | 2.128 | 3.031 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 30,152.44 | 1.657 | 2.034 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 25,284.73 | 1.98 | 2.405 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 23,529.28 | 2.114 | 2.494 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 8,655.44 | 5.798 | 6.324 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 16,880.5 | 2.965 | 3.316 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 8,328.93 | 6.024 | 6.7 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 29,483.9 | 1.695 | 2.033 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 25,239.18 | 1.98 | 2.322 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 23,430.55 | 2.135 | 2.446 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 8,622.79 | 5.801 | 6.525 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 16,748.38 | 2.993 | 3.371 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 8,310.5 | 6.027 | 6.652 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 29,683.57 | 1.683 | 2.026 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 25,130.81 | 1.988 | 2.69 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 23,141.11 | 2.145 | 3.205 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 8,512.74 | 5.832 | 6.841 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 16,543.66 | 3.019 | 3.47 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,991.95 | 6.162 | 8.395 | 0 |

### Environment & System Specifications
- Python: 3.14.7 (CPython)
- OS / Platform: Linux-7.2.2-1-cachyos-x86_64-with-glibc2.44 (x86_64)
- SIMD ISA: SCALAR
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
