"""
Project templates for `des new`.
"""
import os
from pathlib import Path


MINIMAL_APP_PY = """\"\"\"
Minimal Dreaming Electric Sheep application.
\"\"\"
from dreaming_electric_sheep import Application, get, json

app = Application()


@get("/")
async def home():
    return json({"message": "Hello from Dreaming Electric Sheep!"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""

MINIMAL_PYPROJECT = """[project]
name = "{name}"
version = "0.1.0"
description = "A fast web application built with Dreaming Electric Sheep"
requires-python = ">=3.13"
dependencies = [
    "dreaming-electric-sheep[standard]",
]
"""

API_APP_PY = """\"\"\"
REST API application with msgspec validation and OpenAPI support.
\"\"\"
from dreaming_electric_sheep import Application, get, post, json, not_found, ok
from dreaming_electric_sheep.structures import Struct
from typing import List, Optional

app = Application(show_error_details=True)


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
    return json(list(_DB.values()))


@get("/items/{item_id}")
async def get_item(item_id: int):
    item = _DB.get(item_id)
    if item is None:
        return not_found(f"Item with id {item_id} not found")
    return json(item)


@post("/items")
async def create_item(data: Item):
    _DB[data.id] = data
    return ok(json(data))
"""

FULL_APP_PY = """\"\"\"
Full-featured MVC application with DI (rodi), Jinja2 rendering, and service layers.
\"\"\"
from dreaming_electric_sheep import Application, get, post, html, json, ok
from rodi import Container
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = "{name}"
    environment: str = "production"


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

# Configure DI container
services = Container()
services.add_instance(Settings())
services.add_transient(DataService)
app.services = services


@get("/")
async def index(data_svc: DataService):
    stats = data_svc.get_stats()
    return html(f"<h1>Welcome to {stats['app']}</h1><p>Running on {stats['engine']}</p>")


@get("/api/stats")
async def api_stats(data_svc: DataService):
    return json(data_svc.get_stats())
"""


def create_project(project_name: str, template: str = "minimal", target_dir: Path = None):
    if target_dir is None:
        target_dir = Path.cwd() / project_name
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if template == "minimal":
        (target_dir / "app.py").write_text(MINIMAL_APP_PY.replace("{name}", project_name))
        (target_dir / "pyproject.toml").write_text(MINIMAL_PYPROJECT.replace("{name}", project_name))
    elif template == "api":
        (target_dir / "app.py").write_text(API_APP_PY.replace("{name}", project_name))
        (target_dir / "pyproject.toml").write_text(MINIMAL_PYPROJECT.replace("{name}", project_name))
        tests_dir = target_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "test_app.py").write_text("""import pytest
from app import app
from dreaming_electric_sheep.testing import TestClient

@pytest.mark.asyncio
async def test_health():
    client = TestClient(app)
    res = await client.get("/")
    assert res.status == 200
""")
    elif template == "full":
        (target_dir / "app.py").write_text(FULL_APP_PY.replace("{name}", project_name))
        (target_dir / "pyproject.toml").write_text(MINIMAL_PYPROJECT.replace("{name}", project_name))
        templates_dir = target_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        (templates_dir / "index.html").write_text("<!DOCTYPE html><html><body><h1>{{ title }}</h1></body></html>")
    else:
        raise ValueError(f"Unknown template {template!r}. Choose from 'minimal', 'api', 'full'.")

    return target_dir
