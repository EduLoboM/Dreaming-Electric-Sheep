# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-30 18:41:57.
Test parameters: 3 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 117,442.03 | 0.407 | 0.734 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 119,968.02 | 0.392 | 0.711 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 111,049.61 | 0.408 | 0.783 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 64,274.33 | 0.73 | 1.566 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 39,612.05 | 1.223 | 2.281 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 50,652.51 | 0.945 | 1.758 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 87,485.22 | 0.564 | 1.149 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 89,325.22 | 0.542 | 1.041 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 93,172.84 | 0.488 | 1.054 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 54,324.78 | 0.885 | 1.794 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 33,105.94 | 1.432 | 3.106 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 42,095.01 | 1.114 | 2.426 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 96,475.47 | 0.435 | 1.203 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 102,164.5 | 0.42 | 1.204 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 99,582.53 | 0.443 | 1.249 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 50,404.82 | 0.937 | 2.112 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 34,804.92 | 1.393 | 2.488 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 41,960.04 | 1.14 | 2.559 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 80,249.07 | 0.542 | 1.394 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 77,849.88 | 0.555 | 1.502 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 67,812.88 | 0.619 | 1.71 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 40,159.57 | 1.12 | 2.752 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 27,780.58 | 1.647 | 4.092 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 37,844.09 | 1.259 | 2.663 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 62,199.55 | 0.754 | 1.549 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 61,806.62 | 0.75 | 1.592 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 59,050.72 | 0.801 | 1.645 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 38,665.85 | 1.203 | 2.506 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 27,322.5 | 1.712 | 3.542 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 33,610.09 | 1.399 | 2.892 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 104,354.46 | 0.422 | 1.145 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 110,094.59 | 0.406 | 1.111 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 104,913.77 | 0.435 | 1.188 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 50,966.88 | 0.931 | 2.106 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 33,631.5 | 1.42 | 2.974 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 41,765.17 | 1.131 | 2.245 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 77,614.79 | 0.553 | 1.496 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 84,108.49 | 0.526 | 1.408 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 79,872.07 | 0.541 | 1.476 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 43,295.3 | 1.08 | 2.561 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 31,479.62 | 1.524 | 3.29 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 38,154.2 | 1.254 | 2.743 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 63,468.46 | 0.725 | 1.882 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 59,357.17 | 0.79 | 2.112 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 56,625.26 | 0.832 | 2.205 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 29,150.37 | 1.603 | 3.74 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 27,723.31 | 1.737 | 3.382 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 26,811.49 | 1.792 | 3.518 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 48,484.34 | 0.962 | 2.019 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 45,649.5 | 1.012 | 2.09 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 42,668.45 | 1.087 | 2.251 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 24,894.12 | 1.859 | 3.771 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 21,859.37 | 2.156 | 4.357 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 22,372.87 | 2.066 | 4.222 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 32,056.66 | 1.52 | 3.466 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 29,079.95 | 1.685 | 3.604 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 28,693.03 | 1.695 | 3.837 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 19,156.98 | 2.65 | 5.116 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 19,070.02 | 2.716 | 5.521 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 18,024.3 | 2.845 | 5.686 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 36,972.72 | 1.314 | 2.748 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 34,304.65 | 1.387 | 3.036 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 29,963.15 | 1.492 | 3.795 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 18,701.53 | 2.3 | 5.302 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 16,971.41 | 2.819 | 5.093 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 19,039.83 | 2.544 | 4.831 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 24,214.49 | 1.962 | 4.027 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 21,111.89 | 2.241 | 4.337 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 20,591.06 | 2.357 | 4.22 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 7,128.8 | 6.771 | 10.526 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 15,145.84 | 3.229 | 5.045 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 7,445.18 | 6.543 | 9.241 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 26,403.69 | 1.832 | 3.569 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 20,186.34 | 2.255 | 4.402 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 20,537.59 | 2.35 | 4.528 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 7,566.77 | 6.443 | 9.889 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 14,761.25 | 3.309 | 5.327 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 7,083.89 | 6.962 | 9.96 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 23,844.44 | 1.961 | 4.292 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 21,106.09 | 2.274 | 4.418 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 20,740.55 | 2.333 | 3.909 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,701.23 | 6.275 | 8.731 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 13,997.78 | 3.472 | 5.576 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 6,966.64 | 6.812 | 13.256 | 0 |

## Table C: Protocol Comparison (RSGI vs ASGI vs Raw)
Measures the overhead difference between Granian RSGI, Granian ASGI, and Raw Granian ASGI.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 97,176.85 | 0.438 | 1.243 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 100,609.56 | 0.431 | 1.273 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 91,231.89 | 0.474 | 1.363 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 51,154.93 | 0.928 | 1.87 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 33,522.41 | 1.445 | 2.798 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 43,149.26 | 1.114 | 2.022 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 87,279.7 | 0.502 | 1.413 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 87,304.75 | 0.506 | 1.341 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 83,465.94 | 0.543 | 1.478 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 39,118.21 | 1.172 | 2.756 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 31,929.21 | 1.509 | 3.504 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 39,129.73 | 1.229 | 2.576 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 104,154.24 | 0.46 | 0.906 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 104,657.28 | 0.422 | 0.933 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 95,892.64 | 0.464 | 1.099 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 53,387.98 | 0.885 | 1.927 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 34,258.02 | 1.394 | 3.074 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 45,837.87 | 1.049 | 2.093 | 0 |

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
