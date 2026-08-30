# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-30

### Added
- **Native Granian RSGI Protocol Support (v1.6 Spec Compliant)**:
  - Async `__rsgi__` application entry point with high-throughput request/response dispatching.
  - Explicit lifecycle handling with `__rsgi_init__(self, loop)` and `__rsgi_del__(self, loop)` utilizing `loop.run_until_complete`.
  - RSGI Request Freelist integration via `acquire_request` and `release_request` for zero-allocation request object recycling.
  - Direct C API UTF-8 (`PyUnicode_AsUTF8String`) and Latin-1 (`PyUnicode_AsLatin1String`) URL path and query decoding.
  - Spec-compliant `list[tuple[str, str]]` outbound header serialization backed by static intern tables (`_KNOWN_OUTBOUND_HEADER_NAME_STR`, `_KNOWN_OUTBOUND_HEADER_VAL_STR`, `_HEADER_VAL_BYTES`), avoiding runtime `latin-1` decode allocations.

### Changed
- Refactored and optimized RSGI request instantiation and response dispatching directly into the Cython scribe layer (`scribe.pyx`).
- Deduplicated application HTTP dispatch routines and cleaned lifecycle checks.
- Unified comparative benchmark harness (`perf/compare/run.sh`) for single-pass ceiling and stock framework measurements.

### Fixed
- Outbound header format compliance for RSGI servers expecting string tuples rather than raw byte pairs.
- Freelist initialization consistency across cold start and recycled request scopes.

## [1.0.0] - 2026-08-29 :sheep:

- Initial release of **Dreaming Electric Sheep** (high-performance fork of BlackSheep for modern CPython >= 3.13).
- Low-level architectural enhancements: PEP 590 Vectorcall, pure C-struct extension types, memory arena freelists, SIMD vectorization, and zero-copy ASGI dispatch.
- Unified C core (`_des_core`) with singleton intern table, SIMD intrinsics, and 64-byte cacheline-aligned scratchpad arena.
- C `des_err` Result-code style and typed `DesCoreError` exception hierarchy.
