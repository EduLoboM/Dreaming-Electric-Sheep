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

## 🛠️ Developer CLI (`des`)

The `des` CLI is the default, first-class interface for development, inspection, and operations.

### Quick Cheat Sheet

```bash
des new demo -t api          # Scaffold REST API project (Scalar UI default)
cd demo && des dev           # Start development server with auto-reload (http://127.0.0.1:8000)
des run app:app --workers 4  # Start production server (Granian first, Uvicorn fallback)
des check                    # Validate routes, compiled binders, and configuration
des routes                   # Inspect compiled radix routing table
des why GET /items/1         # Explain route match, parameters, binders, and pipeline
des doctor                   # Inspect C-core, SIMD ISA, and runtime environment health
```

### OpenAPI Documentation Model

There is **one** OpenAPI 3.0 specification served at `/openapi.json`. Scalar, Swagger UI, and ReDoc are renderers reading that same spec:

```bash
# Scaffold with your preferred UI renderer
des new demo -t api --docs scalar   # Scalar (default) -> http://127.0.0.1:8000/docs
des new demo -t api --docs swagger  # Swagger UI      -> http://127.0.0.1:8000/docs
des new demo -t api --docs redoc    # ReDoc           -> http://127.0.0.1:8000/docs
```

### Validation Errors (FastAPI-Compatible HTTP 422)

Request validation produces standard, structured JSON errors with explicit field locations:

```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "Expected `float`, got `str`",
      "type": "validation_error"
    }
  ]
}
```

### Server Support & Migration

- **Granian (Default)**: Runs via high-performance **RSGI** protocol by default (`des run` / `des dev`), eliminating ASGI ceremony, with `--interface asgi` supported.
- **Uvicorn**: Supported portable ASGI fallback (`uvicorn app:app --reload`).
- **Docs & Migration**: See [FastAPI to DES Cheat Sheet](docs/fastapi-to-des.md) and [15-Minute Quickstart Tutorial](docs/tutorial.md).

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
```

---

## Benchmarks & Performance Comparison

Localhost framework overhead measured against a shared in-memory fixture (not the TechEmpower Framework Benchmarks; no Postgres). Numbers represent the **median of 3 independent runs** (5s duration each, total 15s sampling per route, 50 concurrency keep-alive connections via `oha` on localhost, 1 worker process).

DES RSGI beats DES ASGI, and beats a raw Granian ASGI script on this box, and stays under raw RSGI.

### Table A: Ceiling Comparison (Apples-to-Apples msgspec Encoder)

Measures framework tax against raw server ceilings when all targets encode JSON per request using `msgspec.json.encode` and run with `optimize_gc=False`.

| Framework | Plaintext (req/s) | JSON (req/s) | Mem get (req/s) | Mem get ×20 (req/s) | HTML fortunes (req/s) | Mem update ×20 (req/s) | Server / Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | 180,418 | 134,066 | 128,959 | 66,668 | 41,258 | 56,284 | Granian (Raw RSGI, 1 worker, msgspec) |
| Granian (Raw ASGI) | 102,600 | 97,707 | 96,067 | 57,577 | 36,136 | 48,356 | Granian (Raw ASGI, 1 worker, msgspec) |
| Dreaming Electric Sheep (RSGI) | 110,538 | 103,517 | 99,210 | 52,074 | 34,669 | 43,834 | Granian (RSGI, 1 worker, msgspec) |
| Dreaming Electric Sheep (ASGI) | 84,070 | 84,287 | 87,052 | 47,839 | 33,576 | 40,628 | Granian (ASGI, 1 worker, msgspec) |
| Uvicorn (Raw ASGI) | 65,440 | 63,618 | 61,350 | 39,702 | 28,271 | 35,110 | Uvicorn (Raw ASGI, 1 worker, msgspec) |

### Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)

Measures out-of-the-box performance using each framework's stock response/serialization helpers (e.g. DES `json()`/`html()`/`text()`, Emmett `json.dumps`, Sanic `json()`, Robyn `jsonify`, Litestar msgspec default, FastAPI `JSONResponse`, Flask `jsonify`/`Response`, Django `JsonResponse`/`HttpResponse`).

| Framework | Plaintext (req/s) | JSON (req/s) | Mem get (req/s) | Mem get ×20 (req/s) | HTML fortunes (req/s) | Mem update ×20 (req/s) | Server / Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Dreaming Electric Sheep (RSGI) | 111,200 | 107,928 | 101,460 | 52,352 | 34,414 | 42,756 | Granian (RSGI, 1 worker, stock helpers) |
| Dreaming Electric Sheep (ASGI) | 87,704 | 86,172 | 84,000 | 45,786 | 27,443 | 35,651 | Granian (ASGI, 1 worker, stock helpers) |
| Emmett | 52,958 | 54,042 | 54,335 | 29,730 | 27,101 | 25,937 | Granian (RSGI/ASGI, 1 worker) |
| Sanic | 49,087 | 44,389 | 42,072 | 24,623 | 21,527 | 22,876 | Sanic (1 worker) |
| Robyn | 32,747 | 29,125 | 28,147 | 16,169 | 15,839 | 16,111 | Robyn Rust (1 worker process) |
| Litestar | 26,852 | 33,040 | 31,644 | 20,380 | 17,956 | 19,849 | Granian (ASGI, 1 worker) |
| FastAPI | 25,289 | 22,176 | 18,999 | 6,180 | 12,872 | 6,977 | Granian (ASGI, 1 worker) |
| Flask | 25,815 | 22,010 | 20,465 | 7,307 | 14,635 | 7,288 | Granian (WSGI, 1 worker) |
| Django | 25,774 | 22,160 | 19,655 | 7,380 | 14,582 | 6,576 | Granian (WSGI, 1 worker, stripped middleware) |

> **Environment & System Specifications**:
>
> - **CPU / OS**: x86_64 Linux (CachyOS Kernel 7.2), SIMD ISA: AVX2
> - **Runtimes**: CPython 3.14.7 | Granian 2.8.2 | Uvicorn 0.34.2 | Emmett 2.8.1 | Sanic 25.12.1 | Robyn 0.88.0 | Litestar 2.24.0 | FastAPI 0.141.1 | Flask 3.1.1 | Django 6.1
> - **Load Tester**: `oha 1.16.0` (Rust)
>
> To reproduce on your machine:
>
> ```bash
> pip install -r perf/requirements-bench.txt
> ./perf/compare/run.sh
> ```

---

<p align="center">
  made with <img src="assets/love.png" width="25" alt="love.png" style="vertical-align: middle;"> by <b>EduLoboM</b>
</p>
