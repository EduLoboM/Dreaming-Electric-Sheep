# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Version Line Policy**: Release `2.6.3` was an upstream version leak from BlackSheep and has been yanked from PyPI. Dreaming Electric Sheep versions remain strictly in the independent `1.x` release line. Upstream BlackSheep version numbers will never be reused.

## [1.2.1] - 2026-09-03

### Fixed
- **Native-str RSGI Headers End-to-End**:
  - Inbound RSGI scope headers and lookups consume and maintain Python `str` without latin-1 bytes conversion or decoding tax.
  - Added Unicode intern table entries in `interning.c` and zero-encoding lookups in `headers.pyx` and `messages.pyx`.
  - Direct pass-through of `str` headers in `send_rsgi_response_sync` outbound.
- **RSGI Mount Dispatching (`MountMixin`)**:
  - Implemented native `__rsgi__` dispatching on `MountMixin` to route requests to mounted child applications.
  - Enhanced `des check` to detect and report mounted applications via `mounted_apps`.

## [1.2.0] - 2026-09-01

### Added
- **First-Class SSR & Pluggable Template Architecture**:
  - `JinjaRenderer` as default SSR engine with auto-escaping, auto-reload, and extensible `Renderer` interface for Mako, Chameleon, and custom DSLs.
  - Native CSRF/antiforgery integration via `csrf_token` / `csrf_input` global functions.
  - Ergonomic response shortcuts: `render(name, **context)`, `render_template(name, **context)`, and `fragment(html_or_template, **context)`.
- **First-Class HTMX Suite**:
  - Request inspection properties: `request.is_htmx`, `request.htmx_target`, `request.htmx_trigger`, `request.htmx_current_url`, `request.htmx_prompt`, `request.htmx_target_id`.
  - HTMX response helpers: `hx_trigger(event, data)`, `hx_redirect(url)`, `hx_refresh()`, `hx_reswap(strategy)`.
- **Real-Time Event Streaming**:
  - `sse_stream` and `ndjson_stream` supporting async generators, sync iterators, and callable providers with automatic client disconnect cleanup.
- **C-Core Fast Query Parser & Scalar Binders**:
  - Zero-allocation C-level query string parser in Cython (`messages.pyx`) via `Request.get_query_param` and `Request.get_query_params`.
  - Direct scalar type conversion (`int`, `float`, `bool`, `str`, `UUID`) in `QueryBinder` and `RouteBinder` bypassing intermediate dict allocations.
- **Microsecond RSGI Hot-Path & C Freelist Pool**:
  - Direct Cython-level object freelist pool (`messages.pyx`) eliminating `threading.local` lookup overhead on the request/response hot path.
  - Native `dispatch_rsgi_http` compiled execution in `scribe.pyx`, reducing framework tax down to ~5.05% vs raw Granian RSGI.
- **Modern Full-Stack CLI Scaffolding (`des new -t fullstack`)**:
  - Scaffold interactive applications with Jinja2, HTMX, Tailwind CSS CDN, debounced search, click-to-edit table rows, and live SSE streaming banner.

## [1.1.2] - 2026-08-31

### Added
- **Native-str RSGI Routing & Header Pipeline**:
  - `routing.pyx`, `scribe.pyx`, `headers.pyx`, and `messages.pyx` consume and emit native `str` on RSGI with zero intermediate byte conversions.
- **Synchronous Handler Normalization**:
  - Direct execution of synchronous route handlers with synchronous parameter binders, avoiding coroutine allocation overhead.
- **Top-Level `des` Package & Agent Guidelines**:
  - Added `des` alias package and `AGENTS.md` / `llms.txt` for AI coding agents and CLI tooling.
  - Project scaffolding (`des new`) with automatic FastAPI-compatible structured `422` validation errors.

### Changed
- Refactored framework tax and benchmarks to accurately document the ~10–15% serving tax on raw Granian RSGI.

## [1.1.1] - 2026-08-31

### Added
- **Zero-Copy Buffers & Fast I/O (`read_buffer`)**:
  - Direct memory buffer access via `Request.read_buffer()` and `Content.read_buffer()` to eliminate copying when interacting with binary payloads or file writes.
- **NDJSON Streaming**:
  - `NDJSONContent` and `ndjson(...)` response helper for high-throughput Newline-Delimited JSON streaming with async and sync iterable support.
- **Enhanced SSE (Server-Sent Events)**:
  - `ServerSentEventsContent` with automatic keep-alive / ping interval, `ServerSentEvent` objects, and graceful client disconnect cleanup.
- **Developer Experience (DX) & Interactive Diagnostics**:
  - Interactive, modern 500 error diagnostic page featuring highlighted code frames, expandable local variable scopes, request headers/context, and environment info.
  - `--debug` flag in `des dev` CLI command to toggle verbose diagnostics and interactive error views.
  - Native `msgspec.Struct` schema generation and model binding in OpenAPI v3 documentation handler.

### Changed
- **Sync-First Vectorcall Fast Path**:
  - Optimized route dispatching for synchronous handlers to bypass unnecessary coroutine/task scheduling overhead.
- **Lazy RSGI Body Allocation**:
  - RSGI request body reading is now lazily deferred until accessed.
- Updated documentation and tutorials with modern examples, SIMD architecture details, and 5-run large-scale benchmark results.

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
