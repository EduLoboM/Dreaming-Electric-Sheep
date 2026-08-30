# FastAPI to Dreaming Electric Sheep (DES) Migration Cheat Sheet

A concise reference table mapping standard FastAPI constructs directly to their high-performance Dreaming Electric Sheep equivalents.

---

## 🚀 Quick Reference Map

| FastAPI | Dreaming Electric Sheep | Note |
| :--- | :--- | :--- |
| `FastAPI()` | `Application()` | Core ASGI & RSGI application instance |
| `@app.get("/path")` | `@get("/path")` | Fast C-radix HTTP handler decorator |
| `@app.post("/path")` | `@post("/path")` | Fast C-radix HTTP handler decorator |
| `Query(default)` | `FromQuery[T]` | Type-validated query parameter |
| `Path(...)` | `FromRoute[T]` or handler arg `item_id: int` | Route path parameter binding |
| `Header(...)` | `FromHeader[T]` | Request header extraction |
| `Cookie(...)` | `FromCookie[T]` | Request cookie extraction |
| `pydantic.BaseModel` | `msgspec.Struct` | High-throughput C/Rust-accelerated struct |
| `body: Item` (Pydantic) | `body: FromJSON[Item]` | Zero-copy / precompiled schema validator |
| `JSONResponse(content)` | `json(content)` | `responses.json()` backed by `msgspec` bytes |
| `HTMLResponse(content)` | `html(content)` | `responses.html()` |
| `PlainTextResponse(content)` | `text(content)` | `responses.text()` |
| `HTTPException(status, detail)` | `HTTPException(status, message)` | Standard HTTP exception |
| `Depends(dependency)` | `app.services.add_transient(Service)` / rodi DI | Pre-bound constructor/handler injection |
| `fastapi dev` / `uvicorn --reload` | `des dev` | Auto-reloading developer server |
| `fastapi run` | `des run app:app` | Production Granian RSGI/ASGI server launcher |

---

## ⚡ Side-by-Side Example

### FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
async def create_item(item: Item):
    if item.price <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    return {"created": item.name, "price": item.price}
```

### Dreaming Electric Sheep

```python
from dreaming_electric_sheep import Application, post, json, FromJSON
from dreaming_electric_sheep.exceptions import BadRequest
from msgspec import Struct

app = Application()

class Item(Struct):
    name: str
    price: float

@post("/items")
async def create_item(item: FromJSON[Item]):
    if item.value.price <= 0:
        raise BadRequest("Price must be positive")
    return json({"created": item.value.name, "price": item.value.price})
```
