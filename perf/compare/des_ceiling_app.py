"""
Dreaming Electric Sheep ceiling benchmark application.
Apples-to-apples encoder comparison with raw ASGI servers (msgspec.json.encode per request).
Runs with optimize_gc=False for fair comparison.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Optional
from jinja2 import Template
import msgspec.json
from dreaming_electric_sheep import Application, Response, Content, get
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

app = Application(optimize_gc=False)

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)
_PLAINTEXT_CONTENT = Content(b"text/plain", b"Hello, World!")
_JSON_CONTENT_TYPE = b"application/json"
_HTML_CONTENT_TYPE = b"text/html; charset=utf-8"


@get("/plaintext")
async def plaintext():
    return Response(200, None, _PLAINTEXT_CONTENT)


@get("/json")
async def handle_json():
    return Response(200, None, Content(_JSON_CONTENT_TYPE, msgspec.json.encode({"message": "Hello, World!"})))


@get("/db")
async def single_query():
    return Response(200, None, Content(_JSON_CONTENT_TYPE, msgspec.json.encode(get_single_world())))


@get("/queries")
async def multiple_queries(queries: Optional[str] = None):
    n = clamp_queries(queries)
    return Response(200, None, Content(_JSON_CONTENT_TYPE, msgspec.json.encode(get_multiple_worlds(n))))


@get("/fortunes")
async def fortunes():
    items = get_fortunes_sorted()
    rendered = _JINJA_TEMPLATE.render(fortunes=items).encode("utf-8")
    return Response(200, None, Content(_HTML_CONTENT_TYPE, rendered))


@get("/updates")
async def data_updates(queries: Optional[str] = None):
    n = clamp_queries(queries)
    return Response(200, None, Content(_JSON_CONTENT_TYPE, msgspec.json.encode(update_multiple_worlds(n))))
