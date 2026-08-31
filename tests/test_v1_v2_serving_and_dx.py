import asyncio
import inspect

import msgspec
import pytest
from openapidocs.v3 import Info

from dreaming_electric_sheep import Application, Content, Request, Response, json, text
from dreaming_electric_sheep.contents import ASGIContent, RSGIContent, StreamedContent
from dreaming_electric_sheep.server.errors import ServerErrorDetailsHandler
from dreaming_electric_sheep.server.openapi.v3 import (
    MsgspecStructTypeHandler,
    OpenAPIHandler,
)
from dreaming_electric_sheep.server.responses import ndjson
from dreaming_electric_sheep.server.sse import (
    JSONLinesResponse,
    NDJSONResponse,
    ServerSentEventsResponse,
    TextServerSentEvent,
)
from dreaming_electric_sheep.testing.messages import MockReceive, MockSend
from tests.test_rsgi import MockRSGIProtocol
from tests.utils.application import FakeApplication


class ItemStruct(msgspec.Struct):
    id: int
    name: str
    price: float = 0.0


@pytest.mark.asyncio
async def test_sync_first_handler_dispatch():
    app = Application()

    @app.router.get("/sync-plaintext")
    def sync_handler(request):
        return text("sync hello")

    @app.router.get("/async-plaintext")
    async def async_handler(request):
        return text("async hello")

    app.router.apply_routes()

    req_sync = Request("GET", b"/sync-plaintext", [])
    res_sync = app.handle(req_sync)
    # Sync handler returns Response directly without coroutine allocation
    assert isinstance(res_sync, Response)
    assert not inspect.isawaitable(res_sync)
    assert res_sync.content.body == b"sync hello"

    req_async = Request("GET", b"/async-plaintext", [])
    res_async = app.handle(req_async)
    # Async handler returns an awaitable
    assert inspect.isawaitable(res_async)
    res_resolved = await res_async
    assert isinstance(res_resolved, Response)
    assert res_resolved.content.body == b"async hello"


@pytest.mark.asyncio
async def test_request_read_buffer_with_bytes_content():
    req = Request("POST", b"/data", [(b"content-type", b"application/octet-stream")])
    raw_bytes = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    req.content = Content(b"application/octet-stream", raw_bytes)

    buf = await req.read_buffer()
    assert isinstance(buf, memoryview)
    assert bytes(buf) == raw_bytes


@pytest.mark.asyncio
async def test_rsgi_content_read_and_read_buffer():
    raw_payload = b"Hello RSGI Buffer Payload"
    proto = MockRSGIProtocol(raw_payload)

    rsgi_content = RSGIContent(proto)
    buf = await rsgi_content.read_buffer()
    assert isinstance(buf, memoryview)
    assert bytes(buf) == raw_payload

    # Calling read() afterwards returns bytes
    b = await rsgi_content.read()
    assert isinstance(b, bytes)
    assert b == raw_payload


@pytest.mark.asyncio
async def test_asgi_content_read_buffer():
    received = False

    async def mock_receive():
        nonlocal received
        if not received:
            received = True
            return {
                "type": "http.request",
                "body": b"ASGI Stream Data",
                "more_body": False,
            }
        return {"type": "http.disconnect"}

    asgi_content = ASGIContent(mock_receive)
    buf = await asgi_content.read_buffer()
    assert isinstance(buf, memoryview)
    assert bytes(buf) == b"ASGI Stream Data"


@pytest.mark.asyncio
async def test_sse_cancellation_calls_aclose():
    aclose_called = False

    async def token_generator():
        try:
            for i in range(10):
                await asyncio.sleep(0.01)
                yield TextServerSentEvent(f"token_{i}")
        finally:
            nonlocal aclose_called
            aclose_called = True

    response = ServerSentEventsResponse(token_generator)
    stream = response.content.stream()

    # Read one chunk then simulate cancellation
    first_chunk = await anext(stream)
    assert b"data: token_0" in first_chunk

    await stream.aclose()
    assert aclose_called is True


@pytest.mark.asyncio
async def test_ndjson_streaming():
    async def items_generator():
        yield {"id": 1, "name": "Alpha"}
        yield {"id": 2, "name": "Beta"}

    response = ndjson(items_generator)
    assert isinstance(response, NDJSONResponse)
    assert response.status == 200

    chunks = []
    async for chunk in response.content.stream():
        chunks.append(chunk)

    full_body = b"".join(chunks)
    lines = [line for line in full_body.split(b"\n") if line]
    assert len(lines) == 2
    assert msgspec.json.decode(lines[0]) == {"id": 1, "name": "Alpha"}
    assert msgspec.json.decode(lines[1]) == {"id": 2, "name": "Beta"}


def test_msgspec_struct_openapi_schema_generation():
    struct_handler = MsgspecStructTypeHandler()
    assert struct_handler.handles_type(ItemStruct) is True

    fields = struct_handler.get_type_fields(ItemStruct, lambda t: None)
    assert len(fields) == 3
    field_names = [f.name for f in fields]
    assert "id" in field_names
    assert "name" in field_names
    assert "price" in field_names


def test_server_error_details_sanitizes_locals():
    handler = ServerErrorDetailsHandler()
    req = Request("GET", b"/failing-route", [])

    secret_token = "SUPER_SECRET_TOKEN_12345"
    normal_var = "visible_debug_value"

    try:
        raise ValueError("Simulated unexpected failure")
    except Exception as exc:
        res = handler.produce_response(req, exc)

    assert res.status == 500
    html_text = res.content.body.decode("utf8")

    # Verify CLI diagnostic callout is present
    assert "des why GET /failing-route" in html_text
    # Verify sensitive tokens are redacted
    assert "SUPER_SECRET_TOKEN_12345" not in html_text
    assert "500 &bull; Internal Server Error" in html_text
