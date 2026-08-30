"""
Robyn benchmark application (default stack).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
from jinja2 import Template
from robyn import Robyn, jsonify, Response, Request
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

app = Robyn(__file__)

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


@app.get("/plaintext")
async def plaintext():
    return "Hello, World!"


@app.get("/json")
async def handle_json():
    return Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        description=jsonify({"message": "Hello, World!"}),
    )


@app.get("/db")
async def single_query():
    return Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        description=jsonify(get_single_world()),
    )


@app.get("/queries")
async def multiple_queries(request: Request):
    q = request.query_params.get("queries", None)
    n = clamp_queries(q)
    return Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        description=jsonify(get_multiple_worlds(n)),
    )


@app.get("/fortunes")
async def fortunes():
    items = get_fortunes_sorted()
    rendered = _JINJA_TEMPLATE.render(fortunes=items)
    return Response(
        status_code=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        description=rendered,
    )


@app.get("/updates")
async def data_updates(request: Request):
    q = request.query_params.get("queries", None)
    n = clamp_queries(q)
    return Response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        description=jsonify(update_multiple_worlds(n)),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--processes", type=int, default=1)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--log-level", type=str, default="WARN")
    parser.add_argument("--disable-openapi", action="store_true")
    args, _ = parser.parse_known_args()
    app.start(host=args.host, port=args.port)
