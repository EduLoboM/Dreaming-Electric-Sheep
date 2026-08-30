# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-30 17:41:17.
Test parameters: 3 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 138,853.92 | 0.337 | 0.664 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 137,811.88 | 0.334 | 0.648 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 113,808.73 | 0.393 | 0.768 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 66,489.04 | 0.719 | 1.478 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 41,632.96 | 1.181 | 1.839 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 57,718.96 | 0.851 | 1.435 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 107,360.14 | 0.428 | 0.883 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 100,360.81 | 0.458 | 0.993 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 87,287.55 | 0.523 | 1.144 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 50,059.94 | 0.888 | 2.141 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 34,577.76 | 1.394 | 2.649 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 42,689.01 | 1.119 | 2.195 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 97,085.4 | 0.492 | 1.233 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 78,760.74 | 0.562 | 1.565 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 77,263.92 | 0.582 | 1.629 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 45,909.46 | 1.036 | 2.055 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 33,416.59 | 1.468 | 2.417 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 40,696.36 | 1.204 | 2.057 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 92,161.45 | 0.481 | 1.272 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 83,733.11 | 0.517 | 1.515 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 86,532.88 | 0.519 | 1.399 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 46,565.28 | 1.031 | 2.39 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 30,906.7 | 1.546 | 3.254 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 37,504.81 | 1.264 | 2.922 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 58,129.55 | 0.8 | 1.734 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 60,000.92 | 0.785 | 1.628 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 60,467.21 | 0.785 | 1.597 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 40,725.53 | 1.164 | 2.409 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 29,581.94 | 1.57 | 3.164 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 36,595.13 | 1.26 | 2.592 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 88,418.04 | 0.52 | 1.42 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 90,435.88 | 0.516 | 1.369 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 82,081.47 | 0.558 | 1.587 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 49,561.84 | 0.984 | 1.534 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 33,656.07 | 1.45 | 2.291 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 39,615.78 | 1.218 | 2.311 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 88,039.3 | 0.51 | 1.3 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 88,357.18 | 0.505 | 1.367 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 75,512.09 | 0.583 | 1.651 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 43,013.74 | 1.093 | 2.551 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 30,974.86 | 1.562 | 3.116 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 37,503.8 | 1.286 | 2.578 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 65,220.27 | 0.723 | 1.798 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 58,313.97 | 0.807 | 2.088 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 55,358.8 | 0.859 | 2.145 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 30,875.98 | 1.575 | 2.886 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 26,780.0 | 1.793 | 3.263 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 27,452.48 | 1.76 | 3.216 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 51,106.75 | 0.914 | 1.878 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 45,731.06 | 1.024 | 2.18 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 43,521.69 | 1.074 | 2.208 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 24,902.72 | 1.891 | 3.841 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 20,617.64 | 2.298 | 4.747 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 22,566.39 | 2.064 | 4.161 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 32,200.88 | 1.547 | 3.21 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 29,348.78 | 1.714 | 3.352 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 29,264.08 | 1.751 | 3.184 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 19,345.92 | 2.672 | 4.914 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 17,508.37 | 2.909 | 5.932 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 17,434.8 | 2.948 | 5.448 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 37,112.5 | 1.299 | 2.723 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 35,599.58 | 1.356 | 2.931 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 32,189.65 | 1.474 | 3.37 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 21,959.87 | 2.207 | 3.685 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 19,151.9 | 2.57 | 3.962 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 20,358.34 | 2.352 | 4.254 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 26,604.87 | 1.837 | 3.086 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 21,278.01 | 2.257 | 4.286 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 20,808.45 | 2.38 | 3.709 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 7,489.51 | 6.596 | 8.558 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 15,236.0 | 3.224 | 4.642 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 7,181.17 | 6.929 | 8.394 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 26,136.13 | 1.872 | 3.216 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 22,371.67 | 2.19 | 3.484 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 20,611.44 | 2.354 | 3.73 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 7,769.33 | 6.421 | 7.486 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 15,174.88 | 3.248 | 4.708 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 7,332.87 | 6.728 | 8.171 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 26,189.72 | 1.863 | 2.972 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 22,070.12 | 2.219 | 3.478 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 20,194.41 | 2.4 | 3.787 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,428.57 | 6.633 | 8.92 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 14,640.61 | 3.324 | 5.352 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,054.26 | 6.911 | 9.094 | 0 |

## Table C: Protocol Comparison (RSGI vs ASGI vs Raw)
Measures the overhead difference between Granian RSGI, Granian ASGI, and Raw Granian ASGI.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 90,330.24 | 0.521 | 1.333 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 89,003.21 | 0.522 | 1.409 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 84,734.35 | 0.554 | 1.45 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 47,377.23 | 1.014 | 1.986 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 32,018.36 | 1.518 | 2.786 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 39,004.97 | 1.232 | 2.342 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 90,393.01 | 0.488 | 1.338 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 86,014.96 | 0.513 | 1.357 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 82,741.63 | 0.544 | 1.462 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 46,379.67 | 1.042 | 2.194 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 32,215.88 | 1.498 | 3.147 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 38,236.29 | 1.255 | 2.521 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 101,373.74 | 0.479 | 0.91 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 106,089.8 | 0.434 | 0.898 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 94,426.72 | 0.478 | 1.036 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 54,553.68 | 0.877 | 1.749 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 33,592.12 | 1.42 | 2.986 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 44,936.96 | 1.076 | 2.053 | 0 |

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
