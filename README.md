<p align="center">
  <img width="420" src="assets/Electric_Screaming_Don_Quixote.png" alt="Dreaming Electric Sheep">
</p>

<h1 align="center">Dreaming Electric Sheep (<code>des</code>)</h1>

<p align="center">
  Dreaming Electric Sheep (<code>des</code>) is a Granian RSGI serving stack you pay a framework tax for startup-compiled <code>msgspec</code> binders, automated OpenAPI documentation from those types, and compile-time request pipeline inspection (<code>des why</code>).
</p>

<p align="center">
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep/actions"><img src="https://img.shields.io/github/actions/workflow/status/EduLoboM/Dreaming-Electric-Sheep/main.yml?style=flat-square" alt="Build"></a>
  <a href="https://pypi.org/project/dreaming-electric-sheep/"><img src="https://img.shields.io/pypi/v/dreaming-electric-sheep.svg?color=blue&style=flat-square" alt="PyPI"></a>
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep"><img src="https://img.shields.io/pypi/pyversions/dreaming-electric-sheep.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://github.com/EduLoboM/Dreaming-Electric-Sheep/blob/main/LICENSE"><img src="https://img.shields.io/github/license/EduLoboM/Dreaming-Electric-Sheep.svg?style=flat-square" alt="License"></a>
</p>

---

## Installation

```bash
pip install "dreaming-electric-sheep[standard]"
```

`[standard]` includes `granian` (RSGI), `typer`, `rich`, `msgspec`, `Jinja2`, and `uvloop` (Linux/macOS).

---

## Quickstart

### 1. Scaffold a project

Create a new REST API project (or use `-t fullstack` for HTMX + Jinja2 as default):

```bash
des new my_api -t api
cd my_api
```

Templates available:

- `-t api`: REST API with `msgspec.Struct` validation and Scalar docs.
- `-t fullstack`: Jinja2 templates, HTMX fragments, Tailwind CDN, and SSE streaming.
- `-t minimal`: Single-file lightweight microservice.

### 2. Start the development server

```bash
des dev
```

The server starts on `http://127.0.0.1:8000` with auto-reload enabled. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Inspect the compiled route pipeline

Verify how routes, parameter decoders, and handlers are resolved at startup:

```bash
des why POST /items
```

Output:

```text
Route:      POST /items
Handler:    app:create_item
Binders:
  • data: FromJSON[CreateItemInput] (pre-compiled msgspec decoder)
OpenAPI:    Documented in /openapi.json (schema: CreateItemInput)
```

---

## Example

Here is a standard `app.py` combining schema validation, automated OpenAPI documentation, and clean route handling:

```python
from des import Application, get, post
from msgspec import Struct

app = Application()

class Item(Struct):
    id: int
    name: str
    price: float

@get("/hello")
def hello():
    return {"message": "Hello from DES!"}

# Pre-compiled msgspec validation with structured 422 errors
@post("/api/items")
def create_item(data: Item):
    return {"status": "created", "item": data}
```

---

## Features

- **Granian RSGI Transport**: Native C/Rust socket communication bypassing ASGI message loop overhead.
- **Pre-Compiled Validation**: `msgspec.Struct` decoders compiled at route registration time; produces standard FastAPI-compatible HTTP 422 errors.
- **Built-in HTMX Suite**: Native helpers (`fragment`, `hx_trigger`, `hx_redirect`, `hx_refresh`) and `sse_stream` / `ndjson_stream`.
- **OpenAPI 3.0 Documentation**: Automatic schema generation with Scalar UI, Swagger UI, and ReDoc support at `/docs`.
- **Developer Introspection**: CLI tools (`des why`, `des routes`, `des doctor`, `des check`) to inspect the routing table and runtime health.

---

## CLI Reference

| Command | Description |
| :--- | :--- |
| `des new <name> -t <template>` | Scaffold a project (`api`, `fullstack`, or `minimal`) |
| `des dev` | Start development server with auto-reload (Granian RSGI) |
| `des run [app] --workers <n>` | Start production server with Granian RSGI |
| `des routes` | Display the compiled radix routing table |
| `des why <METHOD> <PATH>` | Explain route matching, parameter binders, and handler dispatch |
| `des check` | Validate routes, binders, and configuration |
| `des doctor` | Inspect C-extension status and interned memory tables |

---

## Benchmarks

Overhead measured against an in-memory fixture on localhost using `oha` (50 concurrent keep-alive connections, median of 5 runs of 5s each, CPython 3.14 on Linux x86_64, 1 worker process).

### Framework Tax vs. Raw Server Ceilings (msgspec Encoder)

Measures framework overhead against raw server ceilings when all targets encode JSON per request using `msgspec.json.encode` with `optimize_gc=False`. The measured overhead represents the framework cost of route matching, request abstraction, and parameter binding over raw protocol sockets:

| Framework / Layer | Server / Runtime | Plaintext (req/s) | JSON (req/s) | Mem get (req/s) | Mem get ×20 (req/s) | HTML fortunes (req/s) | Mem update ×20 (req/s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Granian (Raw RSGI) | Rust RSGI (ceiling) | 130,148 | 132,491 | 129,247 | 61,794 | 36,078 | 49,109 |
| **Dreaming Electric Sheep (RSGI)** | **Granian (RSGI)** | **128,942** | **123,586** | **121,578** | **59,001** | **32,783** | **47,597** |
| Granian (Raw ASGI) | Rust ASGI (ceiling) | 95,699 | 93,922 | 92,682 | 50,459 | 32,138 | 42,186 |
| Dreaming Electric Sheep (ASGI) | Granian (ASGI) | 88,623 | 88,530 | 80,685 | 46,522 | 29,073 | 38,880 |
| Uvicorn (Raw ASGI) | Uvicorn ASGI (ceiling) | 55,481 | 53,698 | 51,735 | 35,765 | 26,127 | 31,759 |

### Default Stack Comparison (Stock Helpers Out-of-the-Box)

Measures out-of-the-box performance using each framework's standard serialization and response helpers:

| Framework | Server / Runtime | Plaintext (req/s) | JSON (req/s) | Mem get (req/s) | Mem get ×20 (req/s) | HTML fortunes (req/s) | Mem update ×20 (req/s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dreaming Electric Sheep (RSGI)** | **Granian (RSGI)** | **121,069** | **122,107** | **118,083** | **56,176** | **32,432** | **45,328** |
| Dreaming Electric Sheep (ASGI) | Granian (ASGI) | 86,350 | 86,744 | 79,035 | 40,206 | 25,639 | 39,075 |
| Emmett | Granian (RSGI/ASGI) | 57,930 | 52,004 | 50,008 | 24,396 | 22,378 | 21,441 |
| Sanic | Sanic Core | 46,014 | 42,729 | 40,802 | 24,766 | 21,946 | 22,896 |
| Litestar | Granian (ASGI) | 33,523 | 32,140 | 30,722 | 20,600 | 16,695 | 18,930 |
| Robyn | Robyn Rust | 30,885 | 28,311 | 27,791 | 18,921 | 17,786 | 17,727 |
| FastAPI | Granian (ASGI) | 24,231 | 20,367 | 19,050 | 7,389 | 13,518 | 6,858 |
| Django | Granian (WSGI) | 24,018 | 20,238 | 18,763 | 7,281 | 13,456 | 7,011 |
| Flask | Granian (WSGI) | 23,794 | 20,186 | 18,644 | 7,271 | 13,274 | 6,986 |

> See [perf/compare/](perf/compare/) and [Why DES?](docs/why-des.md) for harness scripts and reproduction details.

---

## Documentation

- [15-Minute Tutorial](docs/tutorial.md)
- [Why DES? (Architecture & Trade-offs)](docs/why-des.md)

---

## License & Attribution

Dreaming Electric Sheep is licensed under the [MIT License](LICENSE).  
Derived from [BlackSheep](https://github.com/Neoteroi/BlackSheep) (Copyright (c) Roberto Prevato and contributors). See [NOTICE](NOTICE) for details.

<p align="center">
  made with <img src="assets/love.png" width="20" alt="love" style="vertical-align: middle;"> by <b>EduLoboM</b>
</p>
