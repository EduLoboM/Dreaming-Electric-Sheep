# Why Dreaming Electric Sheep (DES)?

Dreaming Electric Sheep (`des`) is a high-performance CPython 3.13+ serving stack built on top of [Granian](https://github.com/emmett-framework/granian) RSGI.

It does not claim a new computing paradigm. It is an honest, carefully engineered serving stack with a clear operating model: **Granian RSGI + startup-compiled msgspec binders + automated OpenAPI from those types + a CLI that inspects the compiled request graph (`des why`, `des doctor`, `des routes`)**.

---

## The Landscape: Where DES Sits

### 1. DES vs. Raw Granian (RSGI)

Raw Granian written in Rust is the performance ceiling for Python HTTP serving (~180k req/s plaintext). When you build an application directly against raw Granian, you write low-level protocol handlers with manual parsing, no automatic parameter binding, no validation pipeline, no route introspection, and no OpenAPI generation.

**DES is a ~10–15% framework tax you pay on Granian** in exchange for:

1. **Startup-compiled binders**: Request body and parameters decoded into typed objects via pre-compiled `msgspec` decoders with zero runtime reflection.
2. **First-class OpenAPI & UI**: Rich Scalar, Swagger, or ReDoc documentation derived from the exact same typed models.
3. **Compiled-Request Inspection (`des why`)**: A CLI toolchain that inspects radix match routes, bound parameters, and middleware pipelines before sending a single byte.

You will not beat raw Granian while remaining a web framework. The ~10–15% overhead is the price of the framework middle layer. Compared to generic Python frameworks, DES ensures that price is as low as CPython allows.

### 2. DES vs. Litestar

Litestar is a full-featured, mature ASGI framework that already includes `msgspec` integration, dependency injection, and OpenAPI generation.

The distinction in DES is:

- Native **Granian RSGI** first-class protocol integration (eliminating ASGI message ceremony).
- Cython `cdef` core types (`Request`, `Response`, `RouteMatch`, `Header`) backed by C freelists.
- CLI-level compiled request inspector (`des why`) that resolves handler routes, parameter binders, and request lifecycle pipelines at startup.

### 3. DES vs. FastAPI

FastAPI relies on Pydantic validation over standard ASGI (typically Uvicorn). On hot paths, JSON serialization, dictionary transformations, and ASGI task dispatching accumulate overhead.

DES replaces the Pydantic-on-ASGI model with:

- Pre-compiled `msgspec` decoders compiled once during startup.
- Granian RSGI transport by default.
- Fast `cdef` request structures.

This is a structural tax cut on per-request allocations while keeping the familiar FastAPI-shaped DX (identical `422` error shapes, interactive documentation, type-driven routes).
