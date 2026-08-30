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
server = "auto"
"""

ENV_EXAMPLE = """DES_APP=app:app
HOST=127.0.0.1
PORT=8000
"""

MINIMAL_APP_PY = '''"""
Minimal Dreaming Electric Sheep application.
"""
from dreaming_electric_sheep import Application, get, json

app = Application()


@get("/")
async def home():
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
- `des run` - Start production server
"""

API_APP_PY_TEMPLATE = '''"""
REST API application with msgspec validation and OpenAPI documentation.
"""
from typing import List, Optional
from openapidocs.v3 import Info
from dreaming_electric_sheep import Application, get, post, json, not_found, ok
from dreaming_electric_sheep.server.openapi.v3 import OpenAPIHandler
from dreaming_electric_sheep.server.openapi.ui import (
    ScalarUIProvider,
    SwaggerUIProvider,
    ReDocUIProvider,
)
from dreaming_electric_sheep.structures import Struct

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


@get("/")
async def root():
    return json({"status": "healthy", "service": "{name}"})


@get("/items")
async def list_items() -> List[Item]:
    return list(_DB.values())


@get("/items/{item_id}")
async def get_item(item_id: int) -> Item:
    item = _DB.get(item_id)
    if item is None:
        return not_found(f"Item with id {item_id} not found")
    return item


@post("/items")
async def create_item(data: Item) -> Item:
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
- `des run` - Start production server
"""

FULL_APP_PY = '''"""
Full-featured MVC application with DI (rodi), Jinja2 rendering, and service layers.
"""
from pathlib import Path
from dataclasses import dataclass
from jinja2 import FileSystemLoader
from dreaming_electric_sheep import Application, get, json
from dreaming_electric_sheep.server.responses import view
from dreaming_electric_sheep.settings.html import html_settings
from dreaming_electric_sheep.server.rendering.jinja2 import JinjaRenderer


@dataclass
class Settings:
    app_name: str = "{name}"
    environment: str = "development"


class DataService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_stats(self) -> dict:
        return {
            "app": self.settings.app_name,
            "engine": "Dreaming Electric Sheep C Core",
            "active_connections": 42,
        }


app = Application()

# Configure DI container services
app.services.add_instance(Settings())
app.services.add_transient(DataService)

# Configure Jinja2 template loader
html_settings.use(
    JinjaRenderer(loader=FileSystemLoader(Path(__file__).parent / "templates"))
)


@get("/")
async def index(data_svc: DataService):
    stats = data_svc.get_stats()
    return view("index", {"title": f"Welcome to {stats['app']}", "engine": stats["engine"]})


@get("/api/stats")
async def api_stats(data_svc: DataService):
    return json(data_svc.get_stats())
'''

FULL_INDEX_HTML_JINJA = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>Running on {{ engine }}</p>
</body>
</html>
"""

FULL_TEST_PY = """import pytest
from app import app
from dreaming_electric_sheep.testing import TestClient


@pytest.mark.asyncio
async def test_index():
    await app.start()
    client = TestClient(app)
    res = await client.get("/")
    assert res.status == 200
    body = await res.text()
    assert "Welcome" in body


@pytest.mark.asyncio
async def test_api_stats():
    await app.start()
    client = TestClient(app)
    res = await client.get("/api/stats")
    assert res.status == 200
    data = await res.json()
    assert data["active_connections"] == 42
"""

FULL_README = """# {name}

A full-featured MVC web application with DI and Jinja2 rendering built with [Dreaming Electric Sheep](https://github.com/EduLoboM/Dreaming-Electric-Sheep).

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
- `des run` - Start production server
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
        print(f"Error: Directory '{target_dir}' is not empty. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    template = template.lower()

    if docs is not None and template != "api":
        print(f"Error: --docs is only valid with -t api template.", file=sys.stderr)
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Common files
    (target_dir / "pyproject.toml").write_text(GENERIC_PYPROJECT.replace("{name}", project_name), encoding="utf8")
    (target_dir / ".env.example").write_text(ENV_EXAMPLE, encoding="utf8")

    if template == "minimal":
        (target_dir / "app.py").write_text(MINIMAL_APP_PY.replace("{name}", project_name), encoding="utf8")
        (target_dir / "README.md").write_text(MINIMAL_README.replace("{name}", project_name), encoding="utf8")
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
            print(f"Error: Invalid --docs option '{docs_choice}'. Choose from: scalar, swagger, redoc.", file=sys.stderr)
            sys.exit(1)

        app_content = API_APP_PY_TEMPLATE.replace("{name}", project_name).replace("{provider_code}", provider_code)
        (target_dir / "app.py").write_text(app_content, encoding="utf8")
        (target_dir / "README.md").write_text(
            API_README_TEMPLATE.replace("{name}", project_name).replace("{doc_name}", doc_name),
            encoding="utf8",
        )
        (tests_dir / "test_app.py").write_text(API_TEST_PY, encoding="utf8")

    elif template == "full":
        templates_dir = target_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        (templates_dir / "index.jinja").write_text(FULL_INDEX_HTML_JINJA, encoding="utf8")
        (templates_dir / "index.html.jinja").write_text(FULL_INDEX_HTML_JINJA, encoding="utf8")
        (templates_dir / "index.html").write_text(FULL_INDEX_HTML_JINJA, encoding="utf8")

        (target_dir / "app.py").write_text(FULL_APP_PY.replace("{name}", project_name), encoding="utf8")
        (target_dir / "README.md").write_text(FULL_README.replace("{name}", project_name), encoding="utf8")
        (tests_dir / "test_app.py").write_text(FULL_TEST_PY, encoding="utf8")

    else:
        print(f"Error: Unknown template '{template}'. Choose from: minimal, api, full.", file=sys.stderr)
        sys.exit(1)

    return target_dir
