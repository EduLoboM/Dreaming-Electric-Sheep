# Honest ASGI / Web Framework Comparison Results

Generated with `perf/compare/run.sh` on 2026-08-30 12:05:32.
Test parameters: 1 worker process, duration 10s, concurrency 50 keep-alive connections via `oha`.

| framework | route | tool | workers | RPS | p50 ms | p99 ms | errors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep | plaintext | oha | 1 | 32,039.34 | 1.388 | 3.888 | 0 |
| Dreaming Electric Sheep | json | oha | 1 | 27,307.1 | 1.68 | 4.052 | 0 |
| Robyn | plaintext | oha | 1 | 12,114.67 | 4.199 | 7.98 | 0 |
| Robyn | json | oha | 1 | 10,664.65 | 4.611 | 12.205 | 0 |
| Litestar | plaintext | oha | 1 | 14,231.52 | 3.286 | 8.281 | 0 |
| Litestar | json | oha | 1 | 9,446.17 | 4.529 | 12.269 | 0 |
| FastAPI | plaintext | oha | 1 | 7,186.5 | 5.429 | 15.631 | 0 |
| FastAPI | json | oha | 1 | 6,994.55 | 5.826 | 14.693 | 0 |

*Note: Benchmarks measure framework overhead on localhost. Published numbers represent honest local measurements.*
