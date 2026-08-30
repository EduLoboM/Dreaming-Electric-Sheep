"""
Litestar benchmark application (default stack).
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Optional, List, Dict
from jinja2 import Template
from litestar import Litestar, get
from litestar.enums import MediaType
from perf.compare.mock_db import (
    clamp_queries,
    get_single_world,
    get_multiple_worlds,
    get_fortunes_sorted,
    update_multiple_worlds,
    FORTUNES_HTML_TEMPLATE,
)

_JINJA_TEMPLATE = Template(FORTUNES_HTML_TEMPLATE, autoescape=True)


@get("/plaintext", media_type=MediaType.TEXT)
async def plaintext() -> str:
    return "Hello, World!"


@get("/json")
async def handle_json() -> dict:
    return {"message": "Hello, World!"}


@get("/db")
async def single_query() -> Dict[str, int]:
    return get_single_world()


@get("/queries")
async def multiple_queries(queries: Optional[str] = None) -> List[Dict[str, int]]:
    n = clamp_queries(queries)
    return get_multiple_worlds(n)


@get("/fortunes", media_type=MediaType.HTML)
async def fortunes() -> str:
    items = get_fortunes_sorted()
    return _JINJA_TEMPLATE.render(fortunes=items)


@get("/updates")
async def data_updates(queries: Optional[str] = None) -> List[Dict[str, int]]:
    n = clamp_queries(queries)
    return update_multiple_worlds(n)


app = Litestar(
    route_handlers=[
        plaintext,
        handle_json,
        single_query,
        multiple_queries,
        fortunes,
        data_updates,
    ],
    openapi_config=None,
)
