# Dreaming Electric Sheep: The 1-Hour Practical Guide

Dreaming Electric Sheep (DES) is an ultra-fast, high-performance web framework for Python 3.13+ and 3.14+ Free-Threaded (NoGIL) CPython, engineered with C-core SIMD parsing, Cython C-extensions, native RSGI support on Granian, and zero-copy buffers for AI/ML inference serving.

---

## 1. Quickstart & Environment Setup

### Installation

```bash
# Standard installation with Granian server and msgspec serialization
pip install "dreaming-electric-sheep[standard]"

# Or with PyTorch AI/ML serving dependencies
pip install "dreaming-electric-sheep[standard,ml]"
```

Verify your hardware acceleration and SIMD ISA:

```bash
des doctor
```

```text
C CORE & ACCELERATION:
  Shared libdes_core:      LOADED
  Active SIMD ISA:         AVX2 (or SSE2 / NEON / SCALAR)
  Static Intern Table:     0x7fba1000
  Intern Singleton Shared: Shared
  Cython Extensions:       11/11 loaded
```

---

## 2. Scaffold a Project

Use the `des` CLI to scaffold a modern project structure:

```bash
des new inference_service -t api
cd inference_service
```

Project structure:
```text
inference_service/
├── app.py              # Application definition, routes, and OpenAPI config
├── pyproject.toml      # Project configuration and dependencies
├── tests/              # Pytest test suite
│   └── test_app.py
└── README.md
```

Start the development server with auto-reload:

```bash
des dev
```

Interactive OpenAPI documentation is live at:
- **Interactive UI (Scalar)**: `http://127.0.0.1:8000/docs`
- **OpenAPI 3.1 Specification**: `http://127.0.0.1:8000/openapi.json`

---

## 3. High-Performance Hot APIs with `msgspec.Struct`

Dreaming Electric Sheep integrates natively with `msgspec.Struct` for schema validation and C-speed serialization.

```python
from dreaming_electric_sheep import Application, json, status_code
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

@app.router.post("/predict")
def handle_predict(body: PredictRequest) -> PredictResponse:
    # Synchronous handlers return directly with 0 coroutine/task allocations
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

## 4. Zero-Copy AI/ML Tensor Serving (`request.read_buffer()`)

For large binary inputs (raw audio waveforms, image frame buffers, dense embeddings, or float32 feature matrices), Dreaming Electric Sheep provides `await request.read_buffer()`.

This returns a zero-copy Python `memoryview` directly over the network buffer, enabling instant conversion into PyTorch tensors without intermediate `bytes` heap allocations:

```python
from dreaming_electric_sheep import Application, json, Request
import torch

app = Application()

@app.router.post("/v1/embeddings/score")
async def score_embeddings(request: Request):
    # Obtain a zero-copy memoryview over the inbound request body buffer
    buf: memoryview = await request.read_buffer()
    
    # Convert directly to PyTorch tensor without copying bytes
    tensor = torch.frombuffer(buf, dtype=torch.float32).reshape(-1, 768)
    
    # Compute dot product similarity or model inference
    norm = torch.linalg.norm(tensor, dim=1)
    
    return json({
        "batch_size": tensor.shape[0],
        "dim": tensor.shape[1],
        "l2_norm_mean": float(norm.mean().item())
    })
```

---

## 5. Token Streaming with Server-Sent Events (SSE)

For LLM completions and conversational tokens (compatible with OpenAI and vLLM clients), use `ServerSentEventsResponse`. 

If the client disconnects mid-stream, Dreaming Electric Sheep catches `asyncio.CancelledError` and explicitly invokes `aclose()` on your generator, preventing leaked GPU resources:

```python
import asyncio
from dreaming_electric_sheep import Application
from dreaming_electric_sheep.server.sse import ServerSentEventsResponse, TextServerSentEvent

app = Application()

async def generate_tokens(prompt: str):
    tokens = ["Deep ", "learning ", "models ", "dream ", "of ", "electric ", "sheep."]
    for token in tokens:
        await asyncio.sleep(0.05)
        yield TextServerSentEvent(token)

@app.router.get("/v1/chat/completions/stream")
async def chat_stream():
    return ServerSentEventsResponse(lambda: generate_tokens("hello"))
```

---

## 6. High-Throughput Batch Serving with NDJSON (`ndjson`)

For batch evaluation, embeddings streaming, or log ingestion pipelines, use `ndjson`:

```python
import asyncio
from dreaming_electric_sheep import Application
from dreaming_electric_sheep.server.responses import ndjson

app = Application()

async def stream_records():
    for i in range(1000):
        yield {"id": i, "status": "processed", "score": i * 0.01}

@app.router.get("/records.ndjson")
async def get_records():
    return ndjson(stream_records)
```

---

## 7. Developer Experience & Diagnostics

### Interactive Debugging with `debugpy`

Attach VSCode or PyCharm directly to your live service:

```bash
des dev --debug
```

```text
debugpy listening on 0.0.0.0:5678 (ready for debugger attach)
dev http://127.0.0.1:8000 (granian RSGI, reload) (docs: http://127.0.0.1:8000/docs)
```

### Explaining Route Resolution

Use `des why` to inspect how the Cython radix router matches incoming paths:

```bash
des why GET /predict
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

