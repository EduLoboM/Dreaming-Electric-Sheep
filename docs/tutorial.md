# Dreaming Electric Sheep: Practical Guide

## 1. Quickstart & Environment Setup

### Installation

```bash
pip install "dreaming-electric-sheep[standard]"
```

Verify your environment health:

```bash
des doctor
```

```text
C CORE & ENVIRONMENT:
  Shared libdes_core:      LOADED
  Cython Extensions:       11/11 loaded
  Intern Singleton:        Shared
```

---

## 2. Scaffold a Project

Use the `des` CLI to scaffold a modern project structure:

```bash
des new demo -t api
cd demo
```

Project structure:

```text
demo/
├── app.py              # Application definition, routes, and OpenAPI config
├── pyproject.toml      # Project configuration and dependencies
├── tests/              # Pytest test suite
│   └── test_app.py
└── README.md
```

Start the development server with auto-reload (powered by Granian RSGI):

```bash
des dev
```

Interactive OpenAPI documentation is live at:

- **Interactive UI (Scalar)**: `http://127.0.0.1:8000/docs`
- **OpenAPI 3.0 Specification**: `http://127.0.0.1:8000/openapi.json`

---

## 3. High-Performance APIs with `msgspec.Struct`

Dreaming Electric Sheep integrates natively with `msgspec.Struct` for schema validation and C-speed serialization.

```python
from des import Application, get, post
import msgspec

app = Application()

class PredictRequest(msgspec.Struct):
    prompt: str
    max_tokens: int = 128
    temperature: float = 0.7

class PredictResponse(msgspec.Struct):
    text: str
    tokens_generated: int
    latency_ms: float

@post("/predict")
def handle_predict(body: PredictRequest) -> PredictResponse:
    return PredictResponse(
        text=f"Echo: {body.prompt}",
        tokens_generated=len(body.prompt.split()),
        latency_ms=1.42,
    )
```

Test invalid input to inspect the structured `HTTP 422 Unprocessable Entity` validation errors:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "temperature": "high"}'
```

```json
{
  "detail": [
    {
      "loc": ["body", "temperature"],
      "msg": "Expected `float`, got `str`",
      "type": "validation_error"
    }
  ]
}
```

---

## 4. Zero-Copy Buffer Access (`request.read_buffer()`)

For large binary inputs (raw audio waveforms, image frame buffers, dense embeddings, or float32 feature matrices), Dreaming Electric Sheep provides `await request.read_buffer()`.

This returns a zero-copy Python `memoryview` directly over the network buffer:

```python
from des import Application, get, post, json, Request

app = Application()

@post("/v1/embeddings/score")
async def score_embeddings(request: Request):
    # Obtain a zero-copy memoryview over the inbound request body buffer
    buf: memoryview = await request.read_buffer()
    
    return json({
        "received_bytes": len(buf),
    })
```

---

## 5. Token Streaming with Server-Sent Events (SSE)

For LLM completions and conversational tokens, use `ServerSentEventsResponse`.

If the client disconnects mid-stream, Dreaming Electric Sheep catches `asyncio.CancelledError` and explicitly invokes `aclose()` on your generator to release resources cleanly:

```python
import asyncio
from des import Application, get
from dreaming_electric_sheep.server.sse import ServerSentEventsResponse, TextServerSentEvent

app = Application()

async def generate_tokens(prompt: str):
    tokens = ["Deep ", "learning ", "models ", "dream ", "of ", "electric ", "sheep."]
    for token in tokens:
        await asyncio.sleep(0.05)
        yield TextServerSentEvent(token)

@get("/v1/chat/completions/stream")
async def chat_stream():
    return ServerSentEventsResponse(lambda: generate_tokens("hello"))
```

---

## 6. High-Throughput Batch Serving with NDJSON (`ndjson`)

For batch evaluation, embeddings streaming, or log ingestion pipelines, use `ndjson`:

```python
import asyncio
from des import Application, get
from dreaming_electric_sheep.server.responses import ndjson

app = Application()

async def stream_records():
    for i in range(1000):
        yield {"id": i, "status": "processed", "score": i * 0.01}

@get("/records.ndjson")
async def get_records():
    return ndjson(stream_records)
```

---

## 7. Developer Experience & Diagnostics

### Explaining Route Resolution (`des why`)

Use `des why` to inspect how the Cython radix router matches incoming paths and which parameter binders are bound:

```bash
des why POST /predict
```

### Interactive Debugging with `debugpy`

Attach VSCode or PyCharm directly to your live service:

```bash
des dev --debug
```

### Inspecting Rich 500 Diagnostics

When `show_error_details=True` is enabled, unhandled exceptions render a rich diagnostics page with sanitized frame locals and a direct `des why` callout.

---

## 8. Production Deployment

Dreaming Electric Sheep uses Granian with native RSGI bindings for maximum production throughput:

```bash
# Multi-worker production deployment
des run app:app --host 0.0.0.0 --port 8000 --workers 4

# Or using Granian directly
granian --interface rsgi --host 0.0.0.0 --port 8000 --workers 4 app:app
```
