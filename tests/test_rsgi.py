"""
Unit tests for Dreaming Electric Sheep RSGI (Rust Server Gateway Interface) support.
"""
import pytest
from dreaming_electric_sheep import Application, get, post, json, text, html
from dreaming_electric_sheep.structures import Struct
from dreaming_electric_sheep.server.rsgi import instantiate_rsgi_request, send_rsgi_response


class MockRSGIScope:
    def __init__(self, method="GET", path="/", query_string="", headers=None, proto="http"):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.headers = headers or {}
        self.proto = proto
        self.scheme = "http"
        self.http_version = "1.1"
        self.client = "127.0.0.1:54321"


class MockRSGIProtocol:
    def __init__(self, body_to_read=b""):
        self.body_to_read = body_to_read
        self.sent_status = None
        self.sent_headers = None
        self.sent_body = None
        self.response_type = None

    async def __call__(self):
        return self.body_to_read

    def response_bytes(self, status, headers, body):
        self.sent_status = status
        self.sent_headers = headers
        self.sent_body = body
        self.response_type = "bytes"

    def response_str(self, status, headers, body):
        self.sent_status = status
        self.sent_headers = headers
        self.sent_body = body
        self.response_type = "str"

    def response_empty(self, status, headers):
        self.sent_status = status
        self.sent_headers = headers
        self.sent_body = b""
        self.response_type = "empty"


class Item(Struct, frozen=True):
    id: int
    name: str
    price: float


@pytest.mark.asyncio
async def test_rsgi_plaintext_and_json():
    app = Application()

    @get("/plaintext")
    async def pt():
        return text("Hello, World!")

    @get("/json")
    async def js():
        return json({"message": "Hello, World!"})

    app.router.add_get("/plaintext", pt)
    app.router.add_get("/json", js)
    await app.start()

    # 1. Plaintext RSGI call
    scope1 = MockRSGIScope(method="GET", path="/plaintext")
    proto1 = MockRSGIProtocol()
    await app.__rsgi__(scope1, proto1)
    assert proto1.sent_status == 200
    assert proto1.sent_body == b"Hello, World!"

    # 2. JSON RSGI call
    scope2 = MockRSGIScope(method="GET", path="/json")
    proto2 = MockRSGIProtocol()
    await app.__rsgi__(scope2, proto2)
    assert proto2.sent_status == 200
    assert proto2.sent_body == b'{"message":"Hello, World!"}'


@pytest.mark.asyncio
async def test_rsgi_post_and_validation():
    app = Application()

    @post("/items")
    async def create_item(item: Item):
        return json({"id": item.id, "name": item.name, "price": item.price})

    app.router.add_post("/items", create_item)
    await app.start()

    # 1. Valid payload
    valid_payload = b'{"id":1,"name":"Laptop","price":999.50}'
    scope = MockRSGIScope(
        method="POST",
        path="/items",
        headers={"content-type": "application/json"}
    )
    proto = MockRSGIProtocol(body_to_read=valid_payload)
    await app.__rsgi__(scope, proto)
    assert proto.sent_status == 200
    assert b'"name":"Laptop"' in proto.sent_body

    # 2. Invalid payload -> 422 with FastAPI-shaped detail
    invalid_payload = b'{"id":1,"name":"Laptop","price":"invalid"}'
    scope_err = MockRSGIScope(
        method="POST",
        path="/items",
        headers={"content-type": "application/json"}
    )
    proto_err = MockRSGIProtocol(body_to_read=invalid_payload)
    await app.__rsgi__(scope_err, proto_err)
    assert proto_err.sent_status == 422
    assert b'"loc":["body","price"]' in proto_err.sent_body
    assert b'"type":"validation_error"' in proto_err.sent_body
