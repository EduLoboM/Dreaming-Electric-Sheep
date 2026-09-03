# Why Dreaming Electric Sheep (DES)?

Dreaming Electric Sheep (`des`) is a high-performance CPython 3.13+ web stack built directly on top of [Granian](https://github.com/emmett-framework/granian) RSGI.

It does not invent a new computing paradigm. Instead, it is an honest, carefully engineered serving stack built on a clear design philosophy: **combining the raw throughput of Rust/C transport layers with the developer experience of modern typed Python (pre-compiled `msgspec` models, native HTMX reactivity, and compile-time request introspection).**

---

## Core Architectural Pillars

### 1. Granian RSGI Transport vs. ASGI Overhead

Standard Python ASGI frameworks communicate with servers through an asynchronous message loop based on tuples and dictionaries (`receive()` and `send()` coroutines per chunk). This abstraction introduces measurable CPU overhead per request.

DES runs natively on Granian's **RSGI (Rust Server-Gateway Interface)**:

- HTTP requests and responses pass directly between the Rust runtime and Python via C-level function pointers.
- Eliminates ASGI message-loop coroutine scheduling on the hot path.
- Still maintains an ASGI fallback when running in legacy environments or ASGI middleware chains.

### 2. Startup-Compiled Validation (`msgspec`)

Dynamic runtime validation with reflection-heavy libraries can dominate request processing latency.

DES compiles all route decoders and encoders **at application startup**:

- Type annotations (`msgspec.Struct`, dataclasses, typing primitives) are analyzed during route registration.
- Pre-compiled C-speed decoders parse incoming JSON directly into structs with zero dynamic inspection per request.
- Automatic generation of FastAPI-compatible structured `422 Unprocessable Entity` JSON responses on validation errors.

### 3. Cython C-Core & Object Recycling

Every HTTP request creates allocations for request structures, headers, and routing matches:

- Core primitives (`Request`, `Response`, `Header`, `RouteMatch`) are implemented as Cython `cdef` extension types with fixed C struct offsets, eliminating `__dict__` overhead.
- Object freelists recycle request and response instances across HTTP lifecycles to minimize heap allocations and garbage collection pressure.

### 4. Native Full-Stack Reactivity (HTMX + SSR + SSE)

Modern web development increasingly favors server-driven UI over heavy Single Page Application (SPA) bundles.

DES includes first-class primitives for hypermedia architectures:

- HTMX request inspection (`request.is_htmx`, `request.htmx_target`, `request.htmx_trigger`).
- HTMX response helpers (`fragment()`, `hx_trigger()`, `hx_redirect()`, `hx_refresh()`).
- High-throughput Jinja2 rendering engine with a pluggable `Renderer` interface (Mako, Chameleon, MiniJinja).
- Real-time Server-Sent Events (`sse_stream`) and NDJSON streaming (`ndjson_stream`) out of the box.

### 5. Inspectable Runtime (`des why`)

In large applications, understanding how a request reaches a handler and what transformations take place often requires setting breakpoints or digging through layers of decorators.

DES provides startup introspection via the CLI:

- `des why <METHOD> <PATH>`: Traces route matching in the radix tree, parameter binders, and handler dispatch pipeline.
- `des routes`: Visualizes the compiled routing table.
- `des doctor`: Inspects C extensions, intern tables, and runtime environment health.
- `des check`: Validates configuration and routes before deployment.

---

## The Landscape: Where DES Sits

### DES vs. Raw Granian (RSGI)

Raw Granian written in Rust is the performance ceiling for Python HTTP serving. However, writing directly against raw Granian requires writing low-level protocol handlers with manual parsing, manual parameter binding, no route tree, and no automated OpenAPI generation.

DES provides the middle layer with minimal framework overhead in exchange for:

- Radix tree routing with path parameters.
- Startup-compiled `msgspec` request body and query binding.
- Automated OpenAPI 3.0 schemas and interactive UIs (Scalar, Swagger, ReDoc).
- HTMX response helpers and templating integration.

### DES vs. Litestar

Litestar is a mature, feature-rich ASGI framework with built-in `msgspec` support and dependency injection.

DES differs by:

- Operating natively on **Granian RSGI** rather than ASGI by default.
- Using Cython `cdef` extension types with C object freelists for core HTTP objects.
- Offering a compiled request inspection CLI (`des why`) to trace the request pipeline.
- Providing a streamlined full-stack HTMX and SSE workflow built directly into the core library.

### DES vs. FastAPI

FastAPI relies on Pydantic validation over ASGI (typically Uvicorn). On high-throughput routes, JSON serialization, Pydantic model instantiations, and ASGI task dispatching accumulate overhead.

DES provides:

- Pre-compiled `msgspec` decoding instead of dynamic Pydantic reflection.
- Native Granian RSGI transport instead of Uvicorn ASGI.
- Significantly higher out-of-the-box throughput (~4-5x) while retaining the familiar developer experience: identical structured `422` error shapes, automatic OpenAPI docs, and type-annotated routes.
