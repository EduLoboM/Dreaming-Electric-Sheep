<p align="center">
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep/actions"><img src="https://img.shields.io/github/actions/workflow/status/EduLoboM/Dreaming-Electric-Sheep/main.yml?style=for-the-badge" alt="Build"></a>
  <a href="https://pypi.org/project/dreaming-electric-sheep/"><img src="https://img.shields.io/pypi/v/dreaming-electric-sheep.svg?color=blue&style=for-the-badge" alt="pypi"></a>
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep"><img src="https://img.shields.io/pypi/pyversions/dreaming-electric-sheep.svg?style=for-the-badge" alt="versions"></a>
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep/blob/main/LICENSE"><img src="https://img.shields.io/github/license/EduLoboM/Dreaming-Electric-Sheep.svg?style=for-the-badge" alt="license"></a>
</p>

<p align="center">
  <img width="75%" src="assets/Electric_Screaming_Don_Quixote.png" alt="Electric Screaming Don Quixote EGO">
</p>

<h1 align="center">Dreaming Electric Sheep (<code>des</code>)</h1>

**Dreaming Electric Sheep (`des`)** is a high-performance CPython 3.13+ serving stack built on Granian RSGI. It is a ~10–15% tax you pay on raw Granian in exchange for startup-compiled `msgspec` binders, automated OpenAPI documentation, and a CLI that can inspect compiled requests (`des why`, `des doctor`, `des routes`).

See the [15-Minute Quickstart Tutorial](docs/tutorial.md) and [Why DES?](docs/why-des.md) for architectural trade-offs and comparisons with raw Granian, Litestar, and FastAPI.

---

## 🔮 Installation

```bash
pip install "dreaming-electric-sheep[standard]"
```

`[standard]` provides the complete runtime: `granian` (RSGI), `typer`, `rich`, `msgspec`, `Jinja2`, and `uvloop` (Unix).

---

## 🌌 The 3-Minute Hook: See the Compiled Request

### 1. Scaffold and Run

```bash
des new demo -t api && cd demo
des dev
```

### 2. Structured 422 Validation Errors (FastAPI-Compatible)

```bash
curl -X POST http://127.0.0.1:8000/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "price": "invalid"}'
```

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

### 3. Inspect the Compiled Request Pipeline (`des why`)

```bash
des why POST /api/items
```

Inspect route matching, parameter binders, and handler dispatch directly:

```text
Route:      POST /api/items
Handler:    demo.app:create_item
Binders:
  • data: FromJSON[CreateItemInput] (pre-compiled msgspec decoder)
OpenAPI:    Documented in /openapi.json (schema: CreateItemInput)
```

### 4. Interactive OpenAPI 3.0 Documentation

Scalar UI is served automatically at `http://127.0.0.1:8000/docs` reading `/openapi.json`.

---

## 💎 Quick Start

```python
from des import Application, get, post
from msgspec import Struct

# Fast schema-validated msgspec Struct
class CreateItemInput(Struct):
    name: str
    price: float
    tags: list[str] = []

app = Application()

@get("/hello")
def hello():
    return {"message": "Do electric sheep dream of high throughput?"}

@post("/api/items")
def create_item(data: CreateItemInput):
    # Ingested and validated via pre-compiled msgspec decoder
    return {"status": "created", "item": data}
```

Start the application:

```bash
des dev
```

---

## 🧊 Core Architecture & Serving Model

Dreaming Electric Sheep focuses on stripping overhead between the Rust transport layer and Python application code:

1. **Granian RSGI Transport**: Direct `__rsgi__` entrypoint with native request/response passing, bypassing ASGI message loop overhead.
2. **`cdef` Extension Types**: `Request`, `Response`, `Header`, and `RouteMatch` are pure Cython classes with fixed C struct offsets (zero `__dict__` overhead).
3. **C Object Freelists**: `acquire_request` and `release_request` recycle request and response objects across HTTP lifecycles to minimize heap allocations.
4. **Pre-Compiled Type Decoders**: `msgspec` decoders are compiled at startup during route registration, eliminating dynamic reflection in the request path.
5. **Direct Inspection CLI**: `des why`, `des routes`, and `des check` give full visibility into the compiled routing table and parameter binders.

---

## 📗 OpenAPI 3.0 & Interactive UIs

Dreaming Electric Sheep automatically generates OpenAPI 3.0 documentation from type annotations (`msgspec.Struct`, `dataclasses`, `Pydantic`, Python typing) and docstrings.

```python
from des import Application, get
from dreaming_electric_sheep.server.openapi.v3 import OpenAPIHandler
from dreaming_electric_sheep.server.openapi.ui import (
    ScalarUIProvider,
    SwaggerUIProvider,
    ReDocUIProvider,
)
from openapidocs.v3 import Info
from msgspec import Struct

app = Application()

docs = OpenAPIHandler(
    info=Info(title="Dreaming Electric Sheep API", version="1.0.0"),
    ui_providers=[
        ScalarUIProvider("/docs"),      # Scalar UI (default) at /docs
        SwaggerUIProvider("/swagger"),  # Swagger UI at /swagger
        ReDocUIProvider("/redoc"),      # ReDoc at /redoc
    ],
)
docs.bind_app(app)

class Sheep(Struct):
    id: int
    name: str
    voltage: float

@get("/api/sheep/:id")
def get_sheep(id: int) -> Sheep:
    """Retrieve an Electric Sheep by ID."""
    return Sheep(id=id, name="Cloud Sheep", voltage=220.0)
```

---

## ⚡ Developer CLI (`des`)

The `des` CLI is the first-class toolchain for development, inspection, and operations:

```bash
des new demo -t api          # Scaffold REST API project (Scalar UI default)
cd demo && des dev           # Start development server with auto-reload (Granian RSGI)
des run app:app --workers 4  # Start production server (Granian RSGI)
des check                    # Validate routes, compiled binders, and configuration
des routes                   # Inspect compiled radix routing table
des why POST /api/items      # Explain route match, binders, and pipeline
des doctor                   # Inspect C-core, intern tables, and runtime environment
```

---

## 🧱 Dependency Injection & Controllers

Dreaming Electric Sheep includes built-in dependency injection with pre-bound fast dispatching:

```python
from des import Application
from dreaming_electric_sheep.server.controllers import Controller, get

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

## 🏎️ Benchmarks & Framework Tax

Overhead measured against a shared in-memory fixture on localhost (median of 5 independent runs, 5s duration each, 50 concurrent keep-alive connections via `oha`, 1 worker process on CPython 3.14 / Linux x86_64).

### Table A: Framework Tax vs. Raw Server Ceilings (msgspec Encoder)

Measures framework tax against raw server ceilings when all targets encode JSON per request using `msgspec.json.encode` and run with `optimize_gc=False`. The ~10–15% gap represents the necessary cost of route matching, request abstraction, and parameter binding over raw protocol sockets.

| Framework / Layer | Plaintext (req/s) | JSON (req/s) | Mem get (req/s) | Mem get ×20 (req/s) | HTML fortunes (req/s) | Mem update ×20 (req/s) | Server / Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | 162,854 | 154,489 | 150,452 | 75,435 | 44,826 | 60,892 | Raw Granian RSGI (ceiling) |
| **Dreaming Electric Sheep (RSGI)** | **134,822** | **130,907** | **123,133** | **60,569** | **39,401** | **49,647** | **Granian (RSGI, 1 worker)** |
| Granian (Raw ASGI) | 114,973 | 116,875 | 116,221 | 62,999 | 39,310 | 51,302 | Raw Granian ASGI (ceiling) |
| Dreaming Electric Sheep (ASGI) | 103,377 | 101,171 | 98,056 | 51,603 | 35,831 | 43,700 | Granian (ASGI, 1 worker) |
| Uvicorn (Raw ASGI) | 70,525 | 68,868 | 66,042 | 43,252 | 31,085 | 38,358 | Uvicorn (Raw ASGI, 1 worker) |

### Table B: Default Stack Comparison (Stock Helpers Out-of-the-Box)

Measures out-of-the-box performance using each framework's stock response and serialization helpers:

| Framework | Plaintext (req/s) | JSON (req/s) | Mem get (req/s) | Mem get ×20 (req/s) | HTML fortunes (req/s) | Mem update ×20 (req/s) | Server / Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dreaming Electric Sheep (RSGI)** | **132,342** | **130,247** | **122,824** | **60,729** | **38,663** | **49,318** | **Granian (RSGI, 1 worker)** |
| Dreaming Electric Sheep (ASGI) | 103,770 | 101,484 | 97,422 | 51,395 | 35,875 | 43,689 | Granian (ASGI, 1 worker) |
| Emmett | 74,941 | 67,591 | 65,981 | 34,893 | 31,430 | 30,674 | Granian (RSGI/ASGI, 1 worker) |
| Sanic | 52,589 | 47,990 | 45,088 | 26,860 | 23,321 | 24,573 | Sanic (1 worker) |
| Litestar | 40,452 | 38,873 | 37,207 | 25,050 | 20,142 | 22,990 | Granian (ASGI, 1 worker) |
| Robyn | 39,178 | 35,055 | 34,568 | 23,197 | 21,531 | 21,715 | Robyn Rust (1 worker process) |
| FastAPI | 29,253 | 24,622 | 22,815 | 8,515 | 16,376 | 8,186 | Granian (ASGI, 1 worker) |
| Flask | 23,812 | 19,900 | 18,231 | 7,022 | 13,079 | 6,769 | Granian (WSGI, 1 worker) |
| Django | 23,478 | 19,955 | 18,655 | 6,772 | 12,293 | 6,210 | Granian (WSGI, 1 worker) |

> **Environment**: x86_64 Linux, CPython 3.14 | Granian 2.8.2 | Uvicorn 0.34.2 | `oha 1.16.0`. See [perf/compare/](perf/compare/) for harness scripts.

---

## 📕 License & Credits

Dreaming Electric Sheep is released under the [MIT License](LICENSE).
Derived from [BlackSheep](https://github.com/Neoteroi/BlackSheep) (Copyright (C) Roberto Prevato and contributors). See [NOTICE](NOTICE) for attribution.

---

<p align="center">
  made with <img src="assets/love.png" width="25" alt="love.png" style="vertical-align: middle;"> by <b>EduLoboM</b>
</p>
