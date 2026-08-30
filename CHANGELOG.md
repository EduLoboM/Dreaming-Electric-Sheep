# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-29 :sheep:

- Initial release of **Dreaming Electric Sheep** (high-performance fork of BlackSheep for modern CPython >= 3.13).
- Low-level architectural enhancements: PEP 590 Vectorcall, pure C-struct extension types, memory arena freelists, SIMD vectorization, and zero-copy ASGI dispatch.
- Unified C core (`_des_core`) with singleton intern table, SIMD intrinsics, and 64-byte cacheline-aligned scratchpad arena.
- C `des_err` Result-code style and typed `DesCoreError` exception hierarchy.
