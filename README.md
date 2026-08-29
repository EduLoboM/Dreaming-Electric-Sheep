<p align="center">
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep/actions"><img src="https://img.shields.io/github/actions/workflow/status/EduLoboM/Dreaming-Electric-Sheep/main.yml?style=for-the-badge" alt="Build"></a>
  <a href="https://pypi.org/project/dreaming-electric-sheep/"><img src="https://img.shields.io/pypi/v/dreaming-electric-sheep.svg?color=blue&style=for-the-badge" alt="pypi"></a>
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep"><img src="https://img.shields.io/pypi/pyversions/dreaming-electric-sheep.svg?style=for-the-badge" alt="versions"></a>
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep/blob/main/LICENSE"><img src="https://img.shields.io/github/license/EduLoboM/Dreaming-Electric-Sheep.svg?style=for-the-badge" alt="license"></a>
</p>

<p align="center">
  <img width="75%" src="assets/Electric_Screaming_Don_Quixote.png" alt="Electric Screaming Don Quixote EGO">
</p>

<h1 align="center">Dreaming Electric Sheep</h1>

<p align="center">
  <i>"The cloud has a head and two pairs of legs. It resembles a sheep."</i>
</p>

**Dreaming Electric Sheep** is an ultra-high-performance, bare-metal asynchronous ASGI web framework for modern **CPython (3.13–3.14+)**. Born as an aggressively optimized evolution of [BlackSheep](https://github.com/Neoteroi/BlackSheep), it discards legacy runtime compromises (such as PyPy compatibility shims) to squeeze maximum throughput, microsecond-level latency, and direct C/C++/CUDA interoperability from standard CPython.

---

## 🔮 Key Highlights & Low-Level Architectural Features

### 1. 👾 PEP 590 Vectorcall Direct C-API Dispatch

All handler, middleware, and route dispatching bypasses Python `*args` tuple and `**kwargs` dict allocations. Handlers are invoked using `PyObject_Vectorcall` passing contiguous pointer arrays directly in CPU registers.

### 2. ⚓ Pure `cdef class` Extension Types (Zero `__dict__` Overhead)

`Request`, `Response`, `RouteMatch`, `Header`, and `Scope` are pure Cython extension classes. All fields reside at fixed C-level struct offsets (`pointer offset`), eliminating dictionary lookups in the hot path.

### 3. 🌊 C-Level Object Freelists & Fast Pools

`Request` and `Response` instances are managed through dedicated C freelists (`acquire_request`, `release_request`, `acquire_response`, `release_response`), recycling objects across HTTP lifecycles and reducing Python heap pressure to near zero.

### 4. 🚄 SIMD Vectorization (AVX2 / SSE4.2 / ARM NEON / SWAR)

Custom C SIMD kernels accelerate:

- CRLF and header boundary scanning (`\r\n\r\n`).
- URL path separator tokenization (`/`).
- ASCII header validation with fallback SWAR (SIMD Within A Register).

### 5. 🧊 In-Memory Request Scratchpad Arenas

Per-request linear arenas (`scratchpad.h`/`.c`) allow $\mathcal{O}(1)$ allocation and instant bulk resets without invoking `malloc()` or `free()` during request lifecycle processing.

### 6. 💎 Zero-Copy ASGI Ingestion

Direct `bytes-like` memoryview and buffer passing from server transport layers (Granian, Uvicorn) directly into `msgspec` decoders without intermediate string copies or heap duplications.

### 7. 🔋 Pre-Compiled Type Decoders & Fast DI Bindings

Endpoint payload decoders (`msgspec.json.Decoder(type=...)`) and controller activation paths are compiled ahead-of-time during application startup, eradicating runtime reflection.

---

## 🐍 CPython & C / C++ / CUDA Native Interoperability

> [!IMPORTANT]
> **Why CPython exclusively?**
> Dreaming Electric Sheep purposefully removes PyPy and legacy Python support to target modern CPython C-APIs (3.13, 3.14+). If your workloads utilize:
>
> - **C / C++ Native Extensions** (e.g., custom Cython, pybind11, nanobind)
> - **CUDA / TensorRT / PyTorch / ONNX Runtime** for high-throughput AI/ML serving
> - **SIMD hardware intrinsics** (AVX2, AVX-512, NEON)
>
> CPython provides the tightest possible low-overhead binding without JIT tracing overhead or foreign function interface (FFI) penalties.

---

## ⭐ Installation

```bash
pip install dreaming-electric-sheep
```

For maximum throughput and SIMD speed, install with `httptools` and `uvloop`:

```bash
pip install dreaming-electric-sheep httptools uvloop uvicorn granian msgspec
```

---

## ⚡ Quick Start & `msgspec` Integration

Dreaming Electric Sheep provides first-class, zero-overhead support for `msgspec.Struct`, `dataclasses`, and `pydantic` models with startup-cached pre-compiled decoders.

```python
from dreaming_electric_sheep import Application, get, post
from msgspec import Struct

# Fast, schema-validated msgspec Struct
class CreateItemInput(Struct):
    name: str
    price: float
    tags: list[str] = []

app = Application()

@get("/hello")
async def hello():
    return {"message": "Do electric sheep dream of high throughput?"}

@post("/api/items")
async def create_item(data: CreateItemInput):
    # Bound automatically with zero-copy buffer ingestion
    return {"status": "created", "item": data}
```

---

## 📙 OpenAPI 3.0, Swagger UI, Scalar & ReDoc

Dreaming Electric Sheep automatically generates OpenAPI 3.0 documentation from type annotations (`msgspec.Struct`, `dataclasses`, `Pydantic`, Python typing) and docstrings. It includes built-in support for **Swagger UI**, **Scalar**, and **ReDoc**.

```python
from dreaming_electric_sheep import Application, get, post
from dreaming_electric_sheep.server.openapi.v3 import OpenAPIHandler
from dreaming_electric_sheep.server.openapi.ui import (
    SwaggerUIProvider,
    ScalarUIProvider,
    ReDocUIProvider,
)
from openapidocs.v3 import Info
from msgspec import Struct

app = Application()

# Configure OpenAPI with interactive documentation UIs
docs = OpenAPIHandler(
    info=Info(title="Dreaming Electric Sheep API", version="1.0.0"),
    ui_providers=[
        SwaggerUIProvider("/docs"),    # Interactive Swagger UI at /docs
        ScalarUIProvider("/scalar"),   # Modern Scalar UI at /scalar
        ReDocUIProvider("/redoc"),     # ReDoc at /redoc
    ],
)
docs.bind_app(app)

class Sheep(Struct):
    id: int
    name: str
    voltage: float

@get("/api/sheep/:id")
async def get_sheep(id: int) -> Sheep:
    """
    Retrieve an Electric Sheep by ID.
    """
    return Sheep(id=id, name="Cloud Sheep", voltage=220.0)
```

Now navigate in your browser:

- **Swagger UI:** `http://localhost:8000/docs`
- **Scalar UI:** `http://localhost:8000/scalar`
- **ReDoc:** `http://localhost:8000/redoc`
- **Raw OpenAPI JSON Spec:** `http://localhost:8000/openapi.json`

---

## 🔥 High-Speed Serialization: JSON & MessagePack

Take full advantage of pre-compiled type decoders and multiple wire formats:

```python
from dreaming_electric_sheep import Application, FromJSON, FromMsgPack, FromQuery, post
from msgspec import Struct

class SensorPayload(Struct):
    device_id: str
    readings: list[float]

app = Application()

# JSON payload with precompiled type decoder
@post("/api/sensors/json")
async def ingest_json(data: FromJSON[SensorPayload]):
    return {"received_readings": len(data.value.readings)}

# Binary MessagePack payload (ultra-fast binary format)
@post("/api/sensors/msgpack")
async def ingest_msgpack(data: FromMsgPack[SensorPayload]):
    return {"received_readings": len(data.value.readings)}
```

---

## 🚀 Running the Application (CLI & ASGI Servers)

Dreaming Electric Sheep is a standard ASGI 3 application compatible with all ASGI servers.

### 1. Granian (Recommended for Extreme Throughput)

[Granian](https://github.com/emmett-framework/granian) is a high-performance Rust-based HTTP server.

```bash
# Production: Multi-threaded & Multi-worker
granian --interface asgi app:app --port 8000 --workers 4 --threads 2

# Development: Auto-reload
granian --interface asgi app:app --port 8000 --reload
```

### 2. Uvicorn (with `uvloop` & `httptools`)

[Uvicorn](https://www.uvicorn.org/) provides a battle-tested Python/C networking stack.

```bash
# Production: uvloop + httptools
uvicorn app:app --port 8000 --loop uvloop --http httptools --workers 4

# Development: Auto-reload
uvicorn app:app --port 8000 --reload
```

---

## 🎯 Controllers & Dependency Injection

Dreaming Electric Sheep includes built-in dependency injection with pre-bound fast dispatching:

```python
from dreaming_electric_sheep import Application
from dreaming_electric_sheep.server.controllers import Controller, get, post

class DatabaseService:
    def get_stats(self) -> dict:
        return {"active_connections": 42}

app = Application()
app.services.add_singleton(DatabaseService)

class StatusController(Controller):
    @get("/api/status")
    def get_status(self, db: DatabaseService):
        return {"status": "ok", "db": db.get_stats()}

app.controllers.register(StatusController)
```

---

<p align="center">
  made with <img src="assets/love.png" width="18" alt="love.png" style="vertical-align: middle;"> by <b>EduLoboM</b>
</p>
