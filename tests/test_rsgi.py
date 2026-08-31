"""
Unit tests for Dreaming Electric Sheep RSGI (Rust Server Gateway Interface) support.
"""

import pytest

from dreaming_electric_sheep import Application, get, html, json, post, text
from dreaming_electric_sheep.server.rsgi import (
    instantiate_rsgi_request,
    send_rsgi_response,
)
from dreaming_electric_sheep.structures import Struct


class MockRSGIScope:
    def __init__(
        self, method="GET", path="/", query_string="", headers=None, proto="http"
    ):
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
        method="POST", path="/items", headers={"content-type": "application/json"}
    )
    proto = MockRSGIProtocol(body_to_read=valid_payload)
    await app.__rsgi__(scope, proto)
    assert proto.sent_status == 200
    assert b'"name":"Laptop"' in proto.sent_body

    # 2. Invalid payload -> 422 with FastAPI-shaped detail
    invalid_payload = b'{"id":1,"name":"Laptop","price":"invalid"}'
    scope_err = MockRSGIScope(
        method="POST", path="/items", headers={"content-type": "application/json"}
    )
    proto_err = MockRSGIProtocol(body_to_read=invalid_payload)
    await app.__rsgi__(scope_err, proto_err)
    assert proto_err.sent_status == 422
    assert b'"loc":["body","price"]' in proto_err.sent_body
    assert b'"type":"validation_error"' in proto_err.sent_body


def test_rsgi_lifecycle_init_and_del():
    import asyncio

    loop = asyncio.new_event_loop()
    app = Application()
    assert not app.started

    # 1. __rsgi_init__ starts the app using the provided loop
    app.__rsgi_init__(loop)
    assert app.started

    # 2. __rsgi_del__ stops the app using the provided loop
    app.__rsgi_del__(loop)
    assert not app.started
    loop.close()


@pytest.mark.asyncio
async def test_rsgi_unstarted_raises_runtime_error():
    app = Application()
    scope = MockRSGIScope(method="GET", path="/")
    proto = MockRSGIProtocol()
    with pytest.raises(RuntimeError, match="Application has not been started"):
        await app.__rsgi__(scope, proto)


@pytest.mark.asyncio
async def test_rsgi_dynamic_path_and_query_string_and_freelist():
    app = Application()

    @get("/users/{user_id}")
    async def get_user(user_id: int, request):
        token = request.query.get("token", ["none"])[0]
        return json({"user_id": user_id, "token": token})

    app.router.add_get("/users/{user_id}", get_user)
    await app.start()

    # Hit with different dynamic paths and queries to ensure zero-cache correctness
    for i in range(10):
        scope = MockRSGIScope(
            method="GET",
            path=f"/users/{100 + i}",
            query_string=f"token=secret_{i * 7}&extra=1",
            headers={"Host": "example.com", "Accept": "application/json"},
        )
        proto = MockRSGIProtocol()
        await app.__rsgi__(scope, proto)
        assert proto.sent_status == 200
        assert f'"user_id":{100 + i}'.encode() in proto.sent_body
        assert f'"token":"secret_{i * 7}"'.encode() in proto.sent_body


@pytest.mark.asyncio
async def test_rsgi_custom_headers_outbound():
    app = Application()
    from dreaming_electric_sheep import Content, Response

    @get("/custom-headers")
    async def custom_headers():
        resp = Response(
            200,
            [(b"x-custom-key", b"custom-val"), (b"server", b"DES-Test")],
            Content(b"text/plain", b"custom"),
        )
        return resp

    app.router.add_get("/custom-headers", custom_headers)
    await app.start()

    scope = MockRSGIScope(method="GET", path="/custom-headers")
    proto = MockRSGIProtocol()
    await app.__rsgi__(scope, proto)
    assert proto.sent_status == 200
    assert proto.sent_body == b"custom"
    headers_dict = dict(proto.sent_headers)
    assert headers_dict.get("x-custom-key") == "custom-val"
    assert headers_dict.get("server") == "DES-Test"
    assert headers_dict.get("content-type") == "text/plain"


@pytest.mark.asyncio
async def test_rsgi_native_str_headers_inbound_and_outbound():
    app = Application()
    from dreaming_electric_sheep import Content, Response

    @get("/inspect-headers")
    async def inspect_headers(request):
        # Verify str lookups
        auth_str = request.get_first_header("authorization")
        # Verify bytes lookups
        auth_bytes = request.get_first_header(b"authorization")
        # Verify Headers class methods
        ua_str = request.headers.get_first("user-agent")
        ua_bytes = request.headers.get_first(b"user-agent")

        return Response(
            200,
            [("x-echo-auth", auth_str), ("x-echo-ua", ua_str)],
            Content(
                b"application/json",
                json(
                    {"auth_b": auth_bytes.decode(), "ua_b": ua_bytes.decode()}
                ).content.body,
            ),
        )

    app.router.add_get("/inspect-headers", inspect_headers)
    await app.start()

    # Pass native str headers from Granian
    scope = MockRSGIScope(
        method="GET",
        path="/inspect-headers",
        headers=[
            ("authorization", "Bearer token-12345"),
            ("user-agent", "DES-TestAgent/1.0"),
            ("x-forwarded-for", "203.0.113.195"),
        ],
    )
    proto = MockRSGIProtocol()
    await app.__rsgi__(scope, proto)

    assert proto.sent_status == 200
    headers_dict = dict(proto.sent_headers)
    assert headers_dict.get("x-echo-auth") == "Bearer token-12345"
    assert headers_dict.get("x-echo-ua") == "DES-TestAgent/1.0"
    assert b'"auth_b":"Bearer token-12345"' in proto.sent_body
    assert b'"ua_b":"DES-TestAgent/1.0"' in proto.sent_body


@pytest.mark.asyncio
async def test_rsgi_str_zero_encode_pipeline():
    app = Application()

    path_seen = None
    auth_seen = None
    is_path_str = False
    is_auth_str = False

    @get("/native-str/{param}")
    def handler(request, param: str):
        nonlocal path_seen, auth_seen, is_path_str, is_auth_str
        path_seen = request.path
        is_path_str = isinstance(request.path, str)
        auth_seen = request.headers.get_first("authorization")
        is_auth_str = isinstance(auth_seen, str)
        return text(f"param={param}")

    app.router.add_get("/native-str/{param}", handler)
    await app.start()

    # Granian passes str method, str path, str headers
    scope = MockRSGIScope(
        method="GET",
        path="/native-str/foobar",
        query_string="q=1",
        headers=[("authorization", "Bearer token-abc"), ("host", "localhost")],
    )
    proto = MockRSGIProtocol()
    await app.__rsgi__(scope, proto)

    assert proto.sent_status == 200
    assert proto.sent_body == b"param=foobar"
    # Verify request path was native str during handler execution
    assert is_path_str is True
    assert path_seen == "/native-str/foobar"
    # Verify headers were native str during handler execution
    assert is_auth_str is True
    assert auth_seen == "Bearer token-abc"
    # Verify match direct lookup with str
    match = app.router.get_match_by_method_and_path("GET", "/native-str/foobar")
    assert match is not None
    assert match.values == {"param": "foobar"}
    assert isinstance(match.values["param"], str)
