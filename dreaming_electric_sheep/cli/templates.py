"""
Project scaffolding templates for `des new`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

DocsProvider = Literal["scalar", "swagger", "redoc"]

GENERIC_PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
description = "A fast web application built with Dreaming Electric Sheep"
requires-python = ">=3.13"
dependencies = [
    "dreaming-electric-sheep[standard]",
]

[tool.des]
app = "app:app"
host = "127.0.0.1"
port = 8000
server = "granian"
interface = "rsgi"

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
"""

ENV_EXAMPLE = """DES_APP=app:app
HOST=127.0.0.1
PORT=8000
"""

MINIMAL_APP_PY = '''"""
Minimal Dreaming Electric Sheep application.
"""
from des import Application, get, json

app = Application()


@app.router.get("/")
def home():
    return json({"message": "Hello from Dreaming Electric Sheep!"})
'''

MINIMAL_TEST_PY = """import pytest
from app import app
from dreaming_electric_sheep.testing import TestClient


@pytest.mark.asyncio
async def test_home():
    await app.start()
    client = TestClient(app)
    res = await client.get("/")
    assert res.status == 200
    data = await res.json()
    assert data["message"] == "Hello from Dreaming Electric Sheep!"
"""

MINIMAL_README = """# {name}

A minimal web application built with [Dreaming Electric Sheep](https://github.com/EduLoboM/Dreaming-Electric-Sheep).

## Getting Started

```bash
pip install -e ".[standard]"
des dev
```

## Commands

- `des check` - Validate routes and configuration
- `des routes` - List compiled routing table
- `des why GET /` - Explain route matching and handler pipeline
- `des doctor` - System and C-core health
- `des run` - Start production server (Granian RSGI)
"""

API_APP_PY_TEMPLATE = '''"""
REST API application with msgspec validation and OpenAPI documentation.
"""
from typing import List, Optional
from openapidocs.v3 import Info
from des import Application, get, post, json, not_found, ok
from dreaming_electric_sheep.server.openapi.v3 import OpenAPIHandler
from dreaming_electric_sheep.server.openapi.ui import (
    ScalarUIProvider,
    SwaggerUIProvider,
    ReDocUIProvider,
)
from msgspec import Struct

app = Application(show_error_details=True)

# OpenAPI 3.0 configuration (swap provider to change UI clothes):
#   ScalarUIProvider("/docs")  - Modern Scalar reference UI (default)
#   SwaggerUIProvider("/docs") - Classic Swagger UI
#   ReDocUIProvider("/docs")   - Clean ReDoc reading room
docs = OpenAPIHandler(info=Info(title="{name}", version="0.1.0"))
docs.ui_providers = [{provider_code}]
docs.bind_app(app)


class Item(Struct, frozen=True):
    id: int
    name: str
    price: float
    description: Optional[str] = None


_DB: dict[int, Item] = {
    1: Item(id=1, name="Quantum Sheep", price=999.99, description="High performance model"),
    2: Item(id=2, name="Cybernetic RAM", price=149.50, description="DDR5 Neural Module"),
}


@app.router.get("/")
def root():
    return json({"status": "healthy", "service": "{name}"})


@app.router.get("/items")
def list_items() -> List[Item]:
    return list(_DB.values())


@app.router.get("/items/{item_id}")
def get_item(item_id: int) -> Item:
    item = _DB.get(item_id)
    if item is None:
        return not_found(f"Item with id {item_id} not found")
    return item


@app.router.post("/items")
def create_item(data: Item) -> Item:
    _DB[data.id] = data
    return data
'''

API_TEST_PY = """import pytest
from app import app
from dreaming_electric_sheep.contents import JSONContent
from dreaming_electric_sheep.testing import TestClient


@pytest.mark.asyncio
async def test_health():
    await app.start()
    client = TestClient(app)
    res = await client.get("/")
    assert res.status == 200


@pytest.mark.asyncio
async def test_list_items():
    await app.start()
    client = TestClient(app)
    res = await client.get("/items")
    assert res.status == 200
    data = await res.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_item():
    await app.start()
    client = TestClient(app)
    res = await client.get("/items/1")
    assert res.status == 200
    data = await res.json()
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_create_item():
    await app.start()
    client = TestClient(app)
    res = await client.post(
        "/items",
        content=JSONContent({"id": 3, "name": "Neural Link", "price": 499.0}),
    )
    assert res.status == 200
    data = await res.json()
    assert data["name"] == "Neural Link"


@pytest.mark.asyncio
async def test_validation_error_422():
    await app.start()
    client = TestClient(app)
    res = await client.post(
        "/items",
        content=JSONContent({"id": 4, "name": "Invalid Sheep", "price": "not_a_float"}),
    )
    assert res.status == 422
    data = await res.json()
    assert "detail" in data
    assert data["detail"][0]["loc"] == ["body", "price"]
"""

API_README_TEMPLATE = """# {name}

A fast web API built with [Dreaming Electric Sheep](https://github.com/EduLoboM/Dreaming-Electric-Sheep).

## Getting Started

```bash
pip install -e ".[standard]"
des dev
```

```bash
des dev
# Docs   http://127.0.0.1:8000/docs          ({doc_name} by default)
# Spec   http://127.0.0.1:8000/openapi.json
#
# Same spec, different clothes: change the UI provider in app.py
#   SwaggerUIProvider / ScalarUIProvider / ReDocUIProvider
```

## Commands

- `des check` - Validate routes and configuration
- `des routes` - List compiled routing table
- `des why GET /items/1` - Explain route matching and handler pipeline
- `des doctor` - System and C-core health
- `des run` - Start production server (Granian RSGI)
"""

FULLSTACK_APP_PY = '''"""
Full-stack Dreaming Electric Sheep application with Jinja2, HTMX, Tailwind CSS, and SSE streaming.
"""
from pathlib import Path
from typing import List
from msgspec import Struct
from des import (
    Application,
    Request,
    get,
    post,
    put,
    delete,
    render,
    fragment,
    hx_trigger,
    hx_redirect,
    sse_stream,
)
from jinja2 import FileSystemLoader
from dreaming_electric_sheep.settings.html import html_settings
from dreaming_electric_sheep.server.rendering.jinja2 import JinjaRenderer


class Item(Struct):
    id: int
    name: str
    category: str
    price: float


# In-memory storage
_ITEMS: dict[int, Item] = {
    1: Item(id=1, name="Quantum Sheep", category="Robotics", price=999.99),
    2: Item(id=2, name="Cybernetic RAM", category="Hardware", price=149.50),
    3: Item(id=3, name="Neural Interface", category="Bio-Tech", price=499.00),
    4: Item(id=4, name="Photon Emitter", category="Optics", price=89.99),
}

app = Application(show_error_details=True)
html_settings.use(JinjaRenderer(loader=FileSystemLoader(Path(__file__).parent / "templates")))


@app.router.get("/")
def index():
    return render("index.html", items=list(_ITEMS.values()), app_name="{name}")


@app.router.post("/search")
def search(q: str = ""):
    query = q.lower().strip()
    if not query:
        filtered = list(_ITEMS.values())
    else:
        filtered = [
            item for item in _ITEMS.values()
            if query in item.name.lower() or query in item.category.lower()
        ]
    return render("partials/item_rows.html", items=filtered)


@app.router.get("/items/{item_id}/edit")
def edit_item_row(item_id: int):
    item = _ITEMS.get(item_id)
    if item is None:
        return fragment("<tr><td colspan=\'5\' class=\'text-rose-500 py-3 text-center\'>Item not found</td></tr>")
    return render("partials/item_edit_row.html", item=item)


@app.router.get("/items/{item_id}")
def get_item_row(item_id: int):
    item = _ITEMS.get(item_id)
    if item is None:
        return fragment("<tr><td colspan=\'5\' class=\'text-rose-500 py-3 text-center\'>Item not found</td></tr>")
    return render("partials/item_row.html", item=item)


@app.router.put("/items/{item_id}")
def update_item(item_id: int, name: str, category: str, price: float):
    item = _ITEMS.get(item_id)
    if item is None:
        return fragment("<tr><td colspan=\'5\' class=\'text-rose-500 py-3 text-center\'>Item not found</td></tr>")
    updated = Item(id=item_id, name=name, category=category, price=price)
    _ITEMS[item_id] = updated
    resp = render("partials/item_row.html", item=updated)
    return hx_trigger("itemUpdated", {"id": item_id}, resp)


@app.router.get("/events/status")
def status_events():
    async def status_stream():
        import asyncio
        for i in range(1, 10):
            yield f\'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 border border-emerald-500/30 text-emerald-400">● Live Stream Heartbeat #{i}</span>\'
            await asyncio.sleep(1)
    return sse_stream(status_stream)
'''

FULLSTACK_INDEX_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} — Dreaming Electric Sheep Full-Stack</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#f5f3ff',
                            500: '#8b5cf6',
                            600: '#7c3aed',
                            900: '#4c1d95',
                        }
                    }
                }
            }
        }
    </script>
    <!-- HTMX CDN -->
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <script src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased flex flex-col font-sans">
    <header class="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <span class="text-2xl">⚡</span>
                <span class="font-bold text-lg tracking-tight bg-gradient-to-r from-violet-400 to-indigo-300 bg-clip-text text-transparent">{{ app_name }}</span>
                <span class="text-xs px-2 py-0.5 rounded bg-violet-900/40 text-violet-300 border border-violet-700/50 font-mono">Jinja2 + HTMX</span>
            </div>
            <div hx-ext="sse" sse-connect="/events/status" sse-swap="message" class="flex items-center text-xs">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 border border-emerald-500/30 text-emerald-400">● Live Stream Connected</span>
            </div>
        </div>
    </header>

    <main class="max-w-6xl mx-auto px-6 py-10 flex-1 w-full space-y-8">
        <div class="space-y-2">
            <h1 class="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">Hyper-Fast Real-Time Inventory</h1>
            <p class="text-slate-400 max-w-2xl">Powered by Dreaming Electric Sheep C-Core, Jinja2 SSR, and zero-page-refresh HTMX live updates.</p>
        </div>

        <!-- Search Bar -->
        <div class="bg-slate-900/40 p-4 rounded-xl border border-slate-800/80 shadow-lg">
            <div class="relative">
                <input
                    type="text"
                    name="q"
                    placeholder="Search components live (debounce 250ms)..."
                    hx-post="/search"
                    hx-trigger="keyup changed delay:250ms, search"
                    hx-target="#items-table-body"
                    class="w-full bg-slate-950 border border-slate-700/60 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
                />
            </div>
        </div>

        <!-- Interactive Table -->
        <div class="overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/40 shadow-xl">
            <table class="w-full text-left text-sm text-slate-300">
                <thead class="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
                    <tr>
                        <th class="px-6 py-4">ID</th>
                        <th class="px-6 py-4">Name</th>
                        <th class="px-6 py-4">Category</th>
                        <th class="px-6 py-4">Price ($)</th>
                        <th class="px-6 py-4 text-right">Actions</th>
                    </tr>
                </thead>
                <tbody id="items-table-body" class="divide-y divide-slate-800/60 font-mono text-xs sm:text-sm">
                    {% for item in items %}
                    {% include "partials/item_row.html" %}
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </main>

    <footer class="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        Dreaming Electric Sheep — Serving with Granian RSGI & Jinja2 Template Engine.
    </footer>
</body>
</html>
"""

FULLSTACK_ITEM_ROW_HTML = """<tr id="item-{{ item.id }}" class="hover:bg-slate-800/30 transition-colors">
    <td class="px-6 py-4 font-semibold text-violet-400">#{{ item.id }}</td>
    <td class="px-6 py-4 text-slate-100 font-sans font-medium">{{ item.name }}</td>
    <td class="px-6 py-4"><span class="px-2 py-0.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700/50">{{ item.category }}</span></td>
    <td class="px-6 py-4 text-emerald-400">${{ "%.2f" | format(item.price) }}</td>
    <td class="px-6 py-4 text-right">
        <button
            hx-get="/items/{{ item.id }}/edit"
            hx-target="#item-{{ item.id }}"
            hx-swap="outerHTML"
            class="px-3 py-1 bg-violet-600/20 hover:bg-violet-600/40 text-violet-300 border border-violet-500/30 rounded-md text-xs transition-all font-sans font-medium">
            Edit
        </button>
    </td>
</tr>"""

FULLSTACK_ITEM_EDIT_ROW_HTML = """<tr id="item-{{ item.id }}" class="bg-violet-950/20 border border-violet-500/40">
    <td class="px-6 py-4 font-semibold text-violet-400">#{{ item.id }}</td>
    <td class="px-6 py-2">
        <input type="text" name="name" value="{{ item.name }}" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-sm focus:ring-1 focus:ring-violet-500 focus:outline-none">
    </td>
    <td class="px-6 py-2">
        <input type="text" name="category" value="{{ item.category }}" class="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-sm focus:ring-1 focus:ring-violet-500 focus:outline-none">
    </td>
    <td class="px-6 py-2">
        <input type="number" step="0.01" name="price" value="{{ item.price }}" class="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-sm focus:ring-1 focus:ring-violet-500 focus:outline-none font-mono">
    </td>
    <td class="px-6 py-2 text-right space-x-2">
        <button
            hx-put="/items/{{ item.id }}"
            hx-include="#item-{{ item.id }}"
            hx-target="#item-{{ item.id }}"
            hx-swap="outerHTML"
            class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-xs font-sans font-medium transition-all shadow-sm">
            Save
        </button>
        <button
            hx-get="/items/{{ item.id }}"
            hx-target="#item-{{ item.id }}"
            hx-swap="outerHTML"
            class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md text-xs font-sans font-medium transition-all">
            Cancel
        </button>
    </td>
</tr>"""

FULLSTACK_ITEM_ROWS_HTML = """{% for item in items %}
{% include "partials/item_row.html" %}
{% endfor %}"""

FULLSTACK_TEST_PY = """import pytest
from app import app
from dreaming_electric_sheep.testing import TestClient


@pytest.mark.asyncio
async def test_index_page():
    await app.start()
    client = TestClient(app)
    res = await client.get("/")
    assert res.status == 200
    body = await res.text()
    assert "Quantum Sheep" in body
    assert "Jinja2 + HTMX" in body


@pytest.mark.asyncio
async def test_search_live_debounce():
    await app.start()
    client = TestClient(app)
    res = await client.post("/search?q=cyber")
    assert res.status == 200
    body = await res.text()
    assert "Cybernetic RAM" in body
    assert "Photon Emitter" not in body


@pytest.mark.asyncio
async def test_click_to_edit_and_save():
    await app.start()
    client = TestClient(app)

    # Get edit row
    res_edit = await client.get("/items/1/edit")
    assert res_edit.status == 200
    body_edit = await res_edit.text()
    assert 'name="name"' in body_edit
    assert 'value="Quantum Sheep"' in body_edit

    # Save update
    res_save = await client.put("/items/1?name=Super+Quantum+Sheep&category=Robotics&price=1299.99")
    assert res_save.status == 200
    body_save = await res_save.text()
    assert "Super Quantum Sheep" in body_save
    assert "$1299.99" in body_save
    assert res_save.headers.get_first(b"hx-trigger") is not None


@pytest.mark.asyncio
async def test_live_sse_status():
    await app.start()
    client = TestClient(app)
    res = await client.get("/events/status")
    assert res.status == 200
    assert res.headers.get_first(b"content-type") == b"text/event-stream"
"""

FULLSTACK_README = """# {name}

A modern Full-Stack application powered by [Dreaming Electric Sheep](https://github.com/EduLoboM/Dreaming-Electric-Sheep), Jinja2 SSR, HTMX, and Tailwind CSS.

## Features

- **High-Throughput SSR**: Fast template rendering with Jinja2.
- **Zero-SPA Reactivity**: Live search with debounced HTMX swaps, click-to-edit table rows, and real-time SSE stream banner.
- **Granian RSGI**: Default native Rust async runtime.

## Getting Started

```bash
pip install -e ".[standard]"
des dev
```

Visit `http://127.0.0.1:8000/` in your browser.

## Commands

- `des check` - Validate routes and configuration
- `des routes` - List compiled routing table
- `des why GET /` - Explain route matching and handler pipeline
- `des doctor` - System and C-core health
- `des run` - Start production server (Granian RSGI)
"""


def create_project(
    project_name: str,
    template: str = "minimal",
    docs: str | None = None,
    target_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """
    Creates a new project directory with scaffolded files according to the template.
    """
    if target_dir is None:
        target_dir = Path.cwd() / project_name

    target_dir = Path(target_dir).resolve()

    if target_dir.exists() and any(target_dir.iterdir()) and not force:
        print(
            f"Error: Directory '{target_dir}' is not empty. Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(1)

    template = template.lower()

    if docs is not None and template != "api":
        print("Error: --docs is only valid with -t api template.", file=sys.stderr)
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Common files
    (target_dir / "pyproject.toml").write_text(
        GENERIC_PYPROJECT.replace("{name}", project_name), encoding="utf8"
    )
    (target_dir / ".env.example").write_text(ENV_EXAMPLE, encoding="utf8")

    if template == "minimal":
        (target_dir / "app.py").write_text(
            MINIMAL_APP_PY.replace("{name}", project_name), encoding="utf8"
        )
        (target_dir / "README.md").write_text(
            MINIMAL_README.replace("{name}", project_name), encoding="utf8"
        )
        (tests_dir / "test_app.py").write_text(MINIMAL_TEST_PY, encoding="utf8")

    elif template == "api":
        docs_choice = (docs or "scalar").lower()
        if docs_choice == "scalar":
            provider_code = 'ScalarUIProvider("/docs")'
            doc_name = "Scalar"
        elif docs_choice == "swagger":
            provider_code = 'SwaggerUIProvider("/docs")'
            doc_name = "Swagger"
        elif docs_choice == "redoc":
            provider_code = 'ReDocUIProvider("/docs")'
            doc_name = "ReDoc"
        else:
            print(
                f"Error: Invalid --docs option '{docs_choice}'. Choose from: scalar, swagger, redoc.",
                file=sys.stderr,
            )
            sys.exit(1)

        app_content = API_APP_PY_TEMPLATE.replace("{name}", project_name).replace(
            "{provider_code}", provider_code
        )
        (target_dir / "app.py").write_text(app_content, encoding="utf8")
        (target_dir / "README.md").write_text(
            API_README_TEMPLATE.replace("{name}", project_name).replace(
                "{doc_name}", doc_name
            ),
            encoding="utf8",
        )
        (tests_dir / "test_app.py").write_text(API_TEST_PY, encoding="utf8")

    elif template in ("full", "fullstack", "htmx"):
        templates_dir = target_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        partials_dir = templates_dir / "partials"
        partials_dir.mkdir(exist_ok=True)

        (templates_dir / "index.html").write_text(
            FULLSTACK_INDEX_HTML.replace("{name}", project_name), encoding="utf8"
        )
        (partials_dir / "item_row.html").write_text(
            FULLSTACK_ITEM_ROW_HTML, encoding="utf8"
        )
        (partials_dir / "item_edit_row.html").write_text(
            FULLSTACK_ITEM_EDIT_ROW_HTML, encoding="utf8"
        )
        (partials_dir / "item_rows.html").write_text(
            FULLSTACK_ITEM_ROWS_HTML, encoding="utf8"
        )

        (target_dir / "app.py").write_text(
            FULLSTACK_APP_PY.replace("{name}", project_name), encoding="utf8"
        )
        (target_dir / "README.md").write_text(
            FULLSTACK_README.replace("{name}", project_name), encoding="utf8"
        )
        (tests_dir / "test_app.py").write_text(FULLSTACK_TEST_PY, encoding="utf8")

    else:
        print(
            f"Error: Unknown template '{template}'. Choose from: minimal, api, full, fullstack, htmx.",
            file=sys.stderr,
        )
        sys.exit(1)

    return target_dir
