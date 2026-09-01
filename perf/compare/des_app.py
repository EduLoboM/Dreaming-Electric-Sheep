"""
Dreaming Electric Sheep default-stack benchmark application.
Uses stock helpers as shipped (json(), html(), text()), Application(optimize_gc=False).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Optional
from jinja2 import Template
from dreaming_electric_sheep import Application, get, json, text, html
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


@get("/plaintext")
def plaintext():
    return text("Hello, World!")


@get("/json")
def handle_json():
    return json({"message": "Hello, World!"})


@get("/db")
def single_query():
    return json(get_single_world())


@get("/queries")
def multiple_queries(queries: int = 1):
    n = clamp_queries(queries)
    return json(get_multiple_worlds(n))


@get("/fortunes")
def fortunes():
    items = get_fortunes_sorted()
    rendered = _JINJA_TEMPLATE.render(fortunes=items)
    return html(rendered)


@get("/updates")
def data_updates(queries: int = 1):
    n = clamp_queries(queries)
    return json(update_multiple_worlds(n))
