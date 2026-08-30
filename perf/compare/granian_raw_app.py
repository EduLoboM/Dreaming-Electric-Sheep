"""
Raw ASGI benchmark application running directly on Granian.
Measures the pure server overhead ceiling without framework routing/dispatch layers.
Encodes JSON per request using msgspec.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from urllib.parse import parse_qs
from jinja2 import Template
import msgspec.json
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)
_PLAINTEXT_BODY = b"Hello, World!"
_PLAINTEXT_HEADERS = [
    (b"content-type", b"text/plain"),
    (b"content-length", b"13"),
]
_NOT_FOUND_HEADERS = [
    (b"content-type", b"text/plain"),
    (b"content-length", b"9"),
]


async def _handle_plaintext(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": _PLAINTEXT_HEADERS})
    await send({"type": "http.response.body", "body": _PLAINTEXT_BODY})


async def _handle_json(scope, receive, send):
    body = msgspec.json.encode({"message": "Hello, World!"})
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})


async def _handle_db(scope, receive, send):
    body = msgspec.json.encode(get_single_world())
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})


async def _handle_queries(scope, receive, send):
    qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    n = clamp_queries(qs.get("queries", [None])[0])
    body = msgspec.json.encode(get_multiple_worlds(n))
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})


async def _handle_fortunes(scope, receive, send):
    items = get_fortunes_sorted()
    rendered = _JINJA_TEMPLATE.render(fortunes=items).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"text/html; charset=utf-8"),
            (b"content-length", str(len(rendered)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": rendered})


async def _handle_updates(scope, receive, send):
    qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    n = clamp_queries(qs.get("queries", [None])[0])
    body = msgspec.json.encode(update_multiple_worlds(n))
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})


_ROUTES = {
    "/plaintext": _handle_plaintext,
    "/json": _handle_json,
    "/db": _handle_db,
    "/queries": _handle_queries,
    "/fortunes": _handle_fortunes,
    "/updates": _handle_updates,
}


async def app(scope, receive, send):
    if scope["type"] != "http":
        return
    handler = _ROUTES.get(scope.get("path", ""))
    if handler is not None:
        await handler(scope, receive, send)
        return
    await send({"type": "http.response.start", "status": 404, "headers": _NOT_FOUND_HEADERS})
    await send({"type": "http.response.body", "body": b"Not Found"})
