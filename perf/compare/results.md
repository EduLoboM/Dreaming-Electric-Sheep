# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-31 20:33:56.
Test parameters: 5 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 162,854.16 | 0.297 | 0.495 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 154,488.9 | 0.303 | 0.542 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 150,451.79 | 0.304 | 0.609 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 75,434.51 | 0.66 | 0.867 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 44,826.34 | 1.112 | 1.328 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 60,892.17 | 0.816 | 1.125 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 114,973.35 | 0.369 | 0.836 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 116,874.95 | 0.347 | 0.852 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 116,220.94 | 0.354 | 0.92 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 62,998.56 | 0.776 | 1.535 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 39,309.61 | 1.267 | 1.68 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 51,301.57 | 0.962 | 1.71 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 134,822.13 | 0.341 | 0.941 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 130,906.7 | 0.354 | 0.991 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 123,133.31 | 0.382 | 1.073 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 60,568.59 | 0.824 | 1.062 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 39,400.84 | 1.27 | 1.518 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 49,646.92 | 1.004 | 1.234 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 103,376.6 | 0.427 | 1.208 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 101,170.5 | 0.445 | 1.27 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 98,055.97 | 0.472 | 1.333 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 51,603.39 | 0.959 | 1.768 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 35,831.43 | 1.392 | 1.709 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 43,700.27 | 1.131 | 1.664 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 70,525.0 | 0.679 | 1.386 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 68,867.73 | 0.682 | 1.393 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 66,041.94 | 0.723 | 1.473 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 43,252.35 | 1.114 | 2.219 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 31,084.7 | 1.553 | 3.084 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 38,357.62 | 1.253 | 2.488 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 132,342.38 | 0.344 | 0.985 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 130,247.14 | 0.351 | 1.013 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 122,823.63 | 0.378 | 1.089 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 60,728.96 | 0.821 | 1.076 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 38,662.51 | 1.294 | 1.517 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 49,317.7 | 1.012 | 1.251 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 103,770.31 | 0.441 | 1.245 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 101,484.07 | 0.45 | 1.265 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 97,421.9 | 0.477 | 1.328 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 51,395.3 | 0.96 | 1.896 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 35,874.54 | 1.389 | 1.885 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 43,688.72 | 1.13 | 1.903 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 74,941.25 | 0.642 | 1.535 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 67,591.27 | 0.72 | 1.434 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 65,980.58 | 0.743 | 1.641 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 34,893.38 | 1.429 | 2.027 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 31,430.25 | 1.578 | 2.506 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 30,674.43 | 1.625 | 2.293 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 52,589.37 | 0.882 | 1.796 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 47,990.14 | 0.968 | 1.955 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 45,088.44 | 1.038 | 2.066 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 26,859.81 | 1.809 | 3.581 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 23,320.56 | 2.059 | 4.052 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 24,572.77 | 1.959 | 3.832 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 39,177.61 | 1.352 | 2.122 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 35,054.64 | 1.504 | 2.48 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 34,567.71 | 1.532 | 2.483 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 23,197.21 | 2.319 | 3.368 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 21,531.24 | 2.475 | 3.866 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 21,715.23 | 2.471 | 3.535 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 40,451.89 | 1.232 | 1.649 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 38,873.21 | 1.278 | 1.735 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 37,207.1 | 1.34 | 1.734 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 25,049.81 | 1.985 | 2.532 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 20,142.13 | 2.484 | 3.303 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 22,989.65 | 2.165 | 2.513 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 29,253.05 | 1.697 | 2.159 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 24,622.01 | 2.026 | 2.404 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 22,815.4 | 2.186 | 2.594 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 8,514.95 | 5.869 | 6.388 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 16,375.71 | 3.052 | 3.504 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 8,186.49 | 6.12 | 6.581 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 23,811.91 | 1.868 | 3.013 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 19,899.76 | 2.482 | 3.348 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 18,230.7 | 2.695 | 4.263 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 7,021.67 | 7.048 | 8.608 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 13,079.1 | 3.774 | 4.83 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 6,768.89 | 7.346 | 10.536 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 23,477.62 | 2.09 | 3.087 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 19,954.98 | 2.466 | 3.627 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 18,655.29 | 2.645 | 3.492 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 6,771.52 | 7.22 | 10.36 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 12,292.82 | 3.999 | 5.847 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 6,209.89 | 7.976 | 10.842 | 0 |

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
