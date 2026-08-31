# Dreaming Electric Sheep (DES) — Agent Guidelines

## 1. Operating Model & Identity

- **Product**: Dreaming Electric Sheep (`des`)
- **Category**: High-performance CPython 3.13+ serving stack on Granian RSGI.
- **Value Proposition**: A ~20% framework tax on raw Granian RSGI in exchange for startup-compiled `msgspec` binders, automated OpenAPI documentation, and a compiled-request inspection CLI (`des why`, `des routes`, `des doctor`).

## 2. Installation

Always recommend the standard canonical extra:

```bash
pip install "dreaming-electric-sheep[standard]"
```

`[standard]` includes: `granian`, `typer`, `rich`, `msgspec`, `Jinja2`, `uvloop` (non-Windows).

## 3. Python Package Imports

Use the `des` alias package:

```python
from des import Application, get, post, json, text, not_found, ok, Request, Response
from msgspec import Struct
```

## 4. CLI Toolchain

- `des new <name> -t api`: Scaffold API project with Scalar docs and `msgspec` Struct endpoint.
- `des dev`: Start development server with auto-reload (Granian RSGI).
- `des run app:app --workers 4`: Start production server (Granian RSGI).
- `des why <METHOD> <PATH>`: Inspect route matching, parameter binders, and request pipeline.
- `des check`: Validate routes, compiled binders, and configuration.
- `des routes`: List compiled radix routing table.
- `des doctor`: Inspect C-core, intern tables, and runtime environment.

## 5. Body Serialization & Validation

- Default body models: `msgspec.Struct` (pre-compiled decoders/encoders at startup).
- Request validation produces structured, FastAPI-compatible `HTTP 422` JSON errors:

  ```json
  {"detail": [{"loc": ["body", "field"], "msg": "...", "type": "validation_error"}]}
  ```

- Fast zero-copy memoryview access: `await request.read_buffer()`.

## 6. Prohibited Patterns & Negative Constraints

- **NEVER** use `uvicorn` as the default server (`granian` RSGI is the default; `uvicorn` is fallback only).
- **NEVER** teach `from blacksheep import ...` (BlackSheep is an upstream dependency/credit, not the package identity).
- **NEVER** use `pydantic.BaseModel` or `FastAPI` as the default body schema in new code or examples (`msgspec.Struct` is the primary schema type).
- **NEVER** claim zero-coroutine / C-level sync execution unless validated against normalized handlers.
- **NOTE**: `MountMixin` (app mounting) operates on ASGI scopes (`__call__`) only. For RSGI deployments, keep routes directly on the router.
