import asyncio

import msgspec
import pytest

from dreaming_electric_sheep.contents import ASGIContent, Content
from dreaming_electric_sheep.exceptions import MessageAborted
from dreaming_electric_sheep.messages import Request


class ExampleStruct(msgspec.Struct):
    id: int
    name: str


@pytest.mark.asyncio
async def test_zero_copy_asgi_single_chunk_bytes():
    raw_payload = b'{"id": 100, "name": "ZeroCopy"}'

    async def mock_receive():
        return {
            "type": "http.request",
            "body": raw_payload,
            "more_body": False,
        }

    content = ASGIContent(mock_receive)
    body = await content.read()

    # Verify zero-copy: same buffer content
    assert body == raw_payload
    assert content.length == len(raw_payload)

    # Decode directly using msgspec from raw buffer
    decoded = msgspec.json.decode(content.body_buffer, type=ExampleStruct)
    assert decoded.id == 100
    assert decoded.name == "ZeroCopy"


@pytest.mark.asyncio
async def test_zero_copy_asgi_bytearray_and_memoryview():
    raw_payload = bytearray(b'{"id": 42, "name": "MemoryView"}')

    async def mock_receive():
        return {
            "type": "http.request",
            "body": memoryview(raw_payload),
            "more_body": False,
        }

    content = ASGIContent(mock_receive)
    body = await content.read()

    assert bytes(body) == bytes(raw_payload)
    buf = content.body_buffer
    assert isinstance(buf, memoryview)

    decoded = msgspec.json.decode(buf, type=ExampleStruct)
    assert decoded.id == 42
    assert decoded.name == "MemoryView"


@pytest.mark.asyncio
async def test_zero_copy_asgi_multi_chunk_streaming():
    chunks = [b'{"id": 1,', b' "name": ', b'"MultiChunk"}']
    idx = 0

    async def mock_receive():
        nonlocal idx
        chunk = chunks[idx]
        idx += 1
        return {
            "type": "http.request",
            "body": chunk,
            "more_body": idx < len(chunks),
        }

    content = ASGIContent(mock_receive)
    body = await content.read()

    assert body == b'{"id": 1, "name": "MultiChunk"}'
    assert content.length == len(body)

    decoded = msgspec.json.decode(content.body_buffer, type=ExampleStruct)
    assert decoded.id == 1
    assert decoded.name == "MultiChunk"


@pytest.mark.asyncio
async def test_zero_copy_request_body_buffer_and_json():
    raw_payload = b'{"id": 99, "name": "DirectJSON"}'

    async def mock_receive():
        return {
            "type": "http.request",
            "body": raw_payload,
            "more_body": False,
        }

    request = Request("POST", b"/api/test", [(b"content-type", b"application/json")])
    request.content = ASGIContent(mock_receive)

    # Test request.body_buffer
    raw = await request.read_raw()
    assert raw == raw_payload
    buf = request.body_buffer
    assert isinstance(buf, memoryview)
    assert bytes(buf) == raw_payload

    # Test request.json()
    data = await request.json()
    assert data == {"id": 99, "name": "DirectJSON"}


@pytest.mark.asyncio
async def test_read_detached_memory_safety():
    raw_payload = bytearray(b'{"key": "isolated"}')

    async def mock_receive():
        return {
            "type": "http.request",
            "body": raw_payload,
            "more_body": False,
        }

    request = Request("POST", b"/", [(b"content-type", b"application/json")])
    request.content = ASGIContent(mock_receive)

    # Detached copy for background tasks
    detached = await request.read_detached()
    assert isinstance(detached, bytes)
    assert detached == b'{"key": "isolated"}'

    # Modifying original buffer should not mutate detached copy
    raw_payload[2] = ord("X")
    assert detached == b'{"key": "isolated"}'


@pytest.mark.asyncio
async def test_asgi_content_dispose_and_disconnect():
    async def mock_disconnect():
        return {"type": "http.disconnect"}

    content = ASGIContent(mock_disconnect)
    with pytest.raises(MessageAborted):
        await content.read()

    # Test dispose
    content.dispose()
    assert content.receive is None
    assert content.body is None
