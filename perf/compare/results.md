# ASGI / Rust Runtime Framework Benchmark Results

Generated with `perf/compare/run.sh` on 2026-08-30 19:25:23.
Test parameters: 3 runs of 5s per route (median reported), concurrency 50 keep-alive connections via `oha` on localhost.

*Note: Localhost framework overhead + shared in-memory fixture. Not the TechEmpower Framework Benchmarks. No Postgres.*

## Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)
Measures framework tax against raw server ceilings when all targets encode JSON per request using msgspec.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Plaintext | Granian (Raw RSGI, 1 worker, msgspec) | oha | 180,417.82 | 0.267 | 0.443 | 0 |
| Granian (Raw RSGI) | JSON | Granian (Raw RSGI, 1 worker, msgspec) | oha | 134,066.29 | 0.347 | 0.615 | 0 |
| Granian (Raw RSGI) | Mem get | Granian (Raw RSGI, 1 worker, msgspec) | oha | 128,958.77 | 0.348 | 0.674 | 0 |
| Granian (Raw RSGI) | Mem get ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 66,667.98 | 0.717 | 1.396 | 0 |
| Granian (Raw RSGI) | HTML fortunes (in-memory) | Granian (Raw RSGI, 1 worker, msgspec) | oha | 41,257.6 | 1.182 | 2.243 | 0 |
| Granian (Raw RSGI) | Mem update ×20 | Granian (Raw RSGI, 1 worker, msgspec) | oha | 56,284.26 | 0.87 | 1.511 | 0 |
| Granian (Raw ASGI) | Plaintext | Granian (Raw ASGI, 1 worker, msgspec) | oha | 102,599.81 | 0.473 | 0.896 | 0 |
| Granian (Raw ASGI) | JSON | Granian (Raw ASGI, 1 worker, msgspec) | oha | 97,706.76 | 0.487 | 0.948 | 0 |
| Granian (Raw ASGI) | Mem get | Granian (Raw ASGI, 1 worker, msgspec) | oha | 96,066.55 | 0.464 | 0.998 | 0 |
| Granian (Raw ASGI) | Mem get ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 57,577.35 | 0.835 | 1.694 | 0 |
| Granian (Raw ASGI) | HTML fortunes (in-memory) | Granian (Raw ASGI, 1 worker, msgspec) | oha | 36,135.97 | 1.337 | 2.668 | 0 |
| Granian (Raw ASGI) | Mem update ×20 | Granian (Raw ASGI, 1 worker, msgspec) | oha | 48,356.43 | 1.005 | 1.916 | 0 |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, msgspec) | oha | 110,537.68 | 0.401 | 1.082 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, msgspec) | oha | 103,517.13 | 0.422 | 1.168 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, msgspec) | oha | 99,209.7 | 0.451 | 1.266 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 52,074.13 | 0.917 | 1.972 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, msgspec) | oha | 34,668.57 | 1.409 | 2.12 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, msgspec) | oha | 43,833.67 | 1.109 | 2.003 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, msgspec) | oha | 84,070.48 | 0.509 | 1.322 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, msgspec) | oha | 84,287.23 | 0.518 | 1.379 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, msgspec) | oha | 87,052.45 | 0.516 | 1.414 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 47,838.76 | 1.011 | 2.186 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, msgspec) | oha | 33,575.98 | 1.468 | 2.568 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, msgspec) | oha | 40,628.26 | 1.199 | 2.409 | 0 |
| Uvicorn (Raw ASGI) | Plaintext | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 65,440.44 | 0.728 | 1.492 | 0 |
| Uvicorn (Raw ASGI) | JSON | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 63,618.3 | 0.752 | 1.529 | 0 |
| Uvicorn (Raw ASGI) | Mem get | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 61,349.62 | 0.773 | 1.585 | 0 |
| Uvicorn (Raw ASGI) | Mem get ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 39,701.64 | 1.177 | 2.423 | 0 |
| Uvicorn (Raw ASGI) | HTML fortunes (in-memory) | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 28,270.93 | 1.691 | 3.273 | 0 |
| Uvicorn (Raw ASGI) | Mem update ×20 | Uvicorn (Raw ASGI, 1 worker, msgspec) | oha | 35,110.19 | 1.341 | 2.735 | 0 |

## Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)
Measures out-of-the-box performance using each framework's stock response/serialization helpers.

| Framework | Route | Server / Runtime | Tool | RPS (Median) | p50 ms | p99 ms | Errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | Plaintext | Granian (RSGI, 1 worker, stock helpers) | oha | 111,200.11 | 0.403 | 1.107 | 0 |
| Dreaming Electric Sheep (RSGI) | JSON | Granian (RSGI, 1 worker, stock helpers) | oha | 107,927.62 | 0.412 | 1.146 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get | Granian (RSGI, 1 worker, stock helpers) | oha | 101,459.69 | 0.443 | 1.267 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem get ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 52,352.06 | 0.908 | 2.084 | 0 |
| Dreaming Electric Sheep (RSGI) | HTML fortunes (in-memory) | Granian (RSGI, 1 worker, stock helpers) | oha | 34,414.48 | 1.381 | 3.005 | 0 |
| Dreaming Electric Sheep (RSGI) | Mem update ×20 | Granian (RSGI, 1 worker, stock helpers) | oha | 42,755.52 | 1.105 | 2.355 | 0 |
| Dreaming Electric Sheep (ASGI) | Plaintext | Granian (ASGI, 1 worker, stock helpers) | oha | 87,703.73 | 0.497 | 1.33 | 0 |
| Dreaming Electric Sheep (ASGI) | JSON | Granian (ASGI, 1 worker, stock helpers) | oha | 86,172.37 | 0.508 | 1.39 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get | Granian (ASGI, 1 worker, stock helpers) | oha | 83,999.51 | 0.536 | 1.459 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem get ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 45,786.48 | 1.041 | 2.46 | 0 |
| Dreaming Electric Sheep (ASGI) | HTML fortunes (in-memory) | Granian (ASGI, 1 worker, stock helpers) | oha | 27,443.24 | 1.653 | 4.231 | 0 |
| Dreaming Electric Sheep (ASGI) | Mem update ×20 | Granian (ASGI, 1 worker, stock helpers) | oha | 35,650.52 | 1.321 | 2.923 | 0 |
| Emmett | Plaintext | Granian (RSGI/ASGI, 1 worker) | oha | 52,958.08 | 0.789 | 2.746 | 0 |
| Emmett | JSON | Granian (RSGI/ASGI, 1 worker) | oha | 54,042.06 | 0.844 | 2.358 | 0 |
| Emmett | Mem get | Granian (RSGI/ASGI, 1 worker) | oha | 54,334.57 | 0.858 | 2.21 | 0 |
| Emmett | Mem get ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 29,729.62 | 1.592 | 3.535 | 0 |
| Emmett | HTML fortunes (in-memory) | Granian (RSGI/ASGI, 1 worker) | oha | 27,101.16 | 1.765 | 3.535 | 0 |
| Emmett | Mem update ×20 | Granian (RSGI/ASGI, 1 worker) | oha | 25,936.81 | 1.828 | 3.757 | 0 |
| Sanic | Plaintext | Sanic (1 worker) | oha | 49,087.29 | 0.938 | 1.996 | 0 |
| Sanic | JSON | Sanic (1 worker) | oha | 44,388.69 | 1.037 | 2.203 | 0 |
| Sanic | Mem get | Sanic (1 worker) | oha | 42,071.63 | 1.099 | 2.326 | 0 |
| Sanic | Mem get ×20 | Sanic (1 worker) | oha | 24,623.0 | 1.875 | 3.9 | 0 |
| Sanic | HTML fortunes (in-memory) | Sanic (1 worker) | oha | 21,527.34 | 2.14 | 4.39 | 0 |
| Sanic | Mem update ×20 | Sanic (1 worker) | oha | 22,876.06 | 2.049 | 4.158 | 0 |
| Robyn | Plaintext | Robyn Rust (1 worker process) | oha | 32,746.87 | 1.553 | 2.968 | 0 |
| Robyn | JSON | Robyn Rust (1 worker process) | oha | 29,124.68 | 1.744 | 3.346 | 0 |
| Robyn | Mem get | Robyn Rust (1 worker process) | oha | 28,147.49 | 1.792 | 3.863 | 0 |
| Robyn | Mem get ×20 | Robyn Rust (1 worker process) | oha | 16,168.59 | 3.044 | 6.221 | 0 |
| Robyn | HTML fortunes (in-memory) | Robyn Rust (1 worker process) | oha | 15,838.82 | 3.069 | 6.402 | 0 |
| Robyn | Mem update ×20 | Robyn Rust (1 worker process) | oha | 16,111.31 | 3.069 | 6.502 | 0 |
| Litestar | Plaintext | Granian (ASGI, 1 worker) | oha | 26,852.16 | 1.61 | 4.646 | 0 |
| Litestar | JSON | Granian (ASGI, 1 worker) | oha | 33,039.62 | 1.43 | 3.123 | 0 |
| Litestar | Mem get | Granian (ASGI, 1 worker) | oha | 31,643.92 | 1.489 | 3.23 | 0 |
| Litestar | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 20,379.87 | 2.343 | 4.84 | 0 |
| Litestar | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 17,956.17 | 2.66 | 4.901 | 0 |
| Litestar | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 19,849.06 | 2.395 | 4.898 | 0 |
| FastAPI | Plaintext | Granian (ASGI, 1 worker) | oha | 25,289.19 | 1.88 | 3.891 | 0 |
| FastAPI | JSON | Granian (ASGI, 1 worker) | oha | 22,175.61 | 2.168 | 3.881 | 0 |
| FastAPI | Mem get | Granian (ASGI, 1 worker) | oha | 18,998.5 | 2.512 | 4.871 | 0 |
| FastAPI | Mem get ×20 | Granian (ASGI, 1 worker) | oha | 6,180.25 | 7.867 | 12.313 | 0 |
| FastAPI | HTML fortunes (in-memory) | Granian (ASGI, 1 worker) | oha | 12,871.53 | 3.716 | 7.733 | 0 |
| FastAPI | Mem update ×20 | Granian (ASGI, 1 worker) | oha | 6,977.06 | 7.003 | 10.614 | 0 |
| Flask | Plaintext | Granian (WSGI, 1 worker) | oha | 25,814.81 | 1.884 | 3.751 | 0 |
| Flask | JSON | Granian (WSGI, 1 worker) | oha | 22,010.09 | 2.192 | 4.066 | 0 |
| Flask | Mem get | Granian (WSGI, 1 worker) | oha | 20,464.79 | 2.368 | 4.599 | 0 |
| Flask | Mem get ×20 | Granian (WSGI, 1 worker) | oha | 7,307.13 | 6.63 | 11.338 | 0 |
| Flask | HTML fortunes (in-memory) | Granian (WSGI, 1 worker) | oha | 14,634.75 | 3.336 | 5.46 | 0 |
| Flask | Mem update ×20 | Granian (WSGI, 1 worker) | oha | 7,287.53 | 6.695 | 10.007 | 0 |
| Django | Plaintext | Granian (WSGI, 1 worker, stripped middleware) | oha | 25,774.41 | 1.843 | 3.443 | 0 |
| Django | JSON | Granian (WSGI, 1 worker, stripped middleware) | oha | 22,159.79 | 2.183 | 3.809 | 0 |
| Django | Mem get | Granian (WSGI, 1 worker, stripped middleware) | oha | 19,654.9 | 2.44 | 4.395 | 0 |
| Django | Mem get ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 7,379.51 | 6.614 | 9.414 | 0 |
| Django | HTML fortunes (in-memory) | Granian (WSGI, 1 worker, stripped middleware) | oha | 14,582.21 | 3.303 | 5.537 | 0 |
| Django | Mem update ×20 | Granian (WSGI, 1 worker, stripped middleware) | oha | 6,576.22 | 7.38 | 10.639 | 0 |

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
