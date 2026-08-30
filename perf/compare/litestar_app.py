"""
Litestar comparable benchmark application.
"""
from litestar import Litestar, get
from litestar.enums import MediaType


@get("/plaintext", media_type=MediaType.TEXT)
async def plaintext() -> str:
    return "Hello, World!"


@get("/json")
async def handle_json() -> dict:
    return {"message": "Hello, World!"}


app = Litestar(route_handlers=[plaintext, handle_json], openapi_config=None)
