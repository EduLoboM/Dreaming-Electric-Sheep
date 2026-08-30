"""
Raw RSGI benchmark application running directly on Granian.
Measures the pure server RSGI overhead ceiling without framework routing/dispatch layers.
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
_PLAINTEXT_HEADERS = [("content-type", "text/plain")]
_JSON_HEADERS = [("content-type", "application/json")]
_HTML_HEADERS = [("content-type", "text/html; charset=utf-8")]
_NOT_FOUND_HEADERS = [("content-type", "text/plain")]


def _handle_plaintext(scope, protocol):
    protocol.response_bytes(200, _PLAINTEXT_HEADERS, _PLAINTEXT_BODY)


def _handle_json(scope, protocol):
    body = msgspec.json.encode({"message": "Hello, World!"})
    protocol.response_bytes(200, _JSON_HEADERS, body)


def _handle_db(scope, protocol):
    body = msgspec.json.encode(get_single_world())
    protocol.response_bytes(200, _JSON_HEADERS, body)


def _handle_queries(scope, protocol):
    qs = parse_qs(scope.query_string)
    q_val = qs.get("queries", [None])[0]
    n = clamp_queries(q_val)
    body = msgspec.json.encode(get_multiple_worlds(n))
    protocol.response_bytes(200, _JSON_HEADERS, body)


def _handle_fortunes(scope, protocol):
    items = get_fortunes_sorted()
    html_str = _JINJA_TEMPLATE.render(fortunes=items)
    protocol.response_str(200, _HTML_HEADERS, html_str)


def _handle_updates(scope, protocol):
    qs = parse_qs(scope.query_string)
    q_val = qs.get("queries", [None])[0]
    n = clamp_queries(q_val)
    body = msgspec.json.encode(update_multiple_worlds(n))
    protocol.response_bytes(200, _JSON_HEADERS, body)


_ROUTES = {
    "/plaintext": _handle_plaintext,
    "/json": _handle_json,
    "/db": _handle_db,
    "/queries": _handle_queries,
    "/fortunes": _handle_fortunes,
    "/updates": _handle_updates,
}


async def app(scope, protocol):
    handler = _ROUTES.get(scope.path)
    if handler is not None:
        handler(scope, protocol)
    else:
        protocol.response_bytes(404, _NOT_FOUND_HEADERS, b"Not Found")
