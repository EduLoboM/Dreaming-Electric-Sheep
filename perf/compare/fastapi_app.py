"""
FastAPI benchmark application (default stack).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Optional
from jinja2 import Template
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, HTMLResponse
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


@app.get("/plaintext", response_class=PlainTextResponse)
async def plaintext():
    return "Hello, World!"


@app.get("/json")
async def handle_json():
    return {"message": "Hello, World!"}


@app.get("/db")
async def single_query():
    return get_single_world()


@app.get("/queries")
async def multiple_queries(queries: Optional[str] = None):
    n = clamp_queries(queries)
    return get_multiple_worlds(n)


@app.get("/fortunes", response_class=HTMLResponse)
async def fortunes():
    items = get_fortunes_sorted()
    return _JINJA_TEMPLATE.render(fortunes=items)


@app.get("/updates")
async def data_updates(queries: Optional[str] = None):
    n = clamp_queries(queries)
    return update_multiple_worlds(n)
