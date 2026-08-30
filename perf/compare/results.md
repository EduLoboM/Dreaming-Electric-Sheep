# Honest ASGI Framework Comparison Results

Generated with `perf/compare/run.sh` on 2026-08-30 11:59:15.
Test parameters: 1 Granian ASGI worker, duration 10s, concurrency 50 keep-alive connections via `oha`.

| framework | route | tool | workers | RPS | p50 ms | p99 ms | errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep | plaintext | oha | 1 | 26,094.24 | 1.696 | 4.662 | 0 |
| Dreaming Electric Sheep | json | oha | 1 | 22,034.57 | 2.016 | 5.124 | 0 |
| Litestar | plaintext | oha | 1 | 11,953.78 | 3.833 | 10.257 | 0 |
| Litestar | json | oha | 1 | 11,915.7 | 3.932 | 7.798 | 0 |
| FastAPI | plaintext | oha | 1 | 9,259.68 | 5.013 | 11.994 | 0 |
| FastAPI | json | oha | 1 | 8,111.65 | 5.889 | 10.115 | 0 |

*Note: Benchmarks measure framework + Granian overhead on localhost. Published numbers represent honest local measurements.*
