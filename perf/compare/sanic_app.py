"""
Sanic benchmark application (default stack).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Optional
from jinja2 import Template
from sanic import Sanic, Request
from sanic.response import text, json, html
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

app = Sanic("sanic_bench")

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


@app.get("/plaintext")
async def plaintext(request: Request):
    return text("Hello, World!")


@app.get("/json")
async def handle_json(request: Request):
    return json({"message": "Hello, World!"})


@app.get("/db")
async def single_query(request: Request):
    return json(get_single_world())


@app.get("/queries")
async def multiple_queries(request: Request):
    n = clamp_queries(request.args.get("queries"))
    return json(get_multiple_worlds(n))


@app.get("/fortunes")
async def fortunes(request: Request):
    items = get_fortunes_sorted()
    return html(_JINJA_TEMPLATE.render(fortunes=items))


@app.get("/updates")
async def data_updates(request: Request):
    n = clamp_queries(request.args.get("queries"))
    return json(update_multiple_worlds(n))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, single_process=True, access_log=False)
