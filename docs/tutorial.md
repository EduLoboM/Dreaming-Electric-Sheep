# 15-Minute Quickstart Tutorial

Get a production-grade, msgspec-powered REST API running with interactive OpenAPI documentation in minutes.

## 1. Install

```bash
pip install -e ".[standard]"
```

## 2. Scaffold a New Project

```bash
des new demo -t api
cd demo
```

This creates a structured project with `app.py`, test suite, and modern Scalar OpenAPI UI at `/docs`.

## 3. Start the Development Server

```bash
des dev
```

The dev server starts with auto-reload at `http://127.0.0.1:8000`.
- **API Spec**: `http://127.0.0.1:8000/openapi.json`
- **Interactive UI**: `http://127.0.0.1:8000/docs`

> *Portability Note*: You can also run standard ASGI servers directly: `uvicorn app:app --reload` or `granian --interface asgi app:app --reload`.

## 4. Inspect the Application with `des` CLI

```bash
des check                     # Verify routes, compiled binders, and settings
des routes                    # View compiled radix routing table
des why GET /items/1          # Explain route matching and parameter resolution
des doctor                    # Inspect C-core, SIMD ISA, and runtime health
```

## 5. Structured 422 Validation Errors

If a client sends invalid JSON types to `POST /items`:

```bash
curl -X POST http://127.0.0.1:8000/items \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "name": "Quantum Core", "price": "invalid"}'
```

Response (`HTTP 422 Unprocessable Entity`):

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

## 6. Run Production Server

```bash
des run app:app --workers 4
```

Granian with native RSGI interface is selected automatically for maximum throughput, with seamless fallback to Uvicorn ASGI.
