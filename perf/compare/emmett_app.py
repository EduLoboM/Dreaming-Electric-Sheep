"""
Emmett benchmark application (default stack).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pkgutil
import importlib.util
import json
from jinja2 import Template

# Compatibility shim for Python 3.14 where pkgutil.get_loader was removed
if not hasattr(pkgutil, "get_loader"):
    def _compat_get_loader(name: str):
        try:
            spec = importlib.util.find_spec(name)
            return getattr(spec, "loader", None) if spec else None
        except Exception:
            return None
    pkgutil.get_loader = _compat_get_loader  # type: ignore

from emmett import App, response, request
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

app = App(__name__, root_path=".")

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


@app.route("/plaintext", output="str")
async def plaintext():
    response.content_type = "text/plain; charset=utf-8"
    return "Hello, World!"


@app.route("/json", output="str")
async def handle_json():
    response.content_type = "application/json"
    return json.dumps({"message": "Hello, World!"})


@app.route("/db", output="str")
async def single_query():
    response.content_type = "application/json"
    return json.dumps(get_single_world())


@app.route("/queries", output="str")
async def multiple_queries():
    response.content_type = "application/json"
    n = clamp_queries(request.query_params.queries)
    return json.dumps(get_multiple_worlds(n))


@app.route("/fortunes", output="str")
async def fortunes():
    response.content_type = "text/html; charset=utf-8"
    items = get_fortunes_sorted()
    return _JINJA_TEMPLATE.render(fortunes=items)


@app.route("/updates", output="str")
async def data_updates():
    response.content_type = "application/json"
    n = clamp_queries(request.query_params.queries)
    return json.dumps(update_multiple_worlds(n))
