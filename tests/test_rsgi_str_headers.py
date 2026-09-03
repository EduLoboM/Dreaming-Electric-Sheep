"""
Strict tests verifying Ticket A (native-str RSGI headers end-to-end),
Ticket M (MountMixin RSGI dispatching), and Ticket D (documentation gates).
"""

import re
import pytest

from dreaming_electric_sheep import Application, Content, Response, get, text
from dreaming_electric_sheep.messages import acquire_request
from dreaming_electric_sheep.server.application import MountMixin
from dreaming_electric_sheep.server.rsgi import (
    instantiate_rsgi_request,
    send_rsgi_response_sync,
)


class MockRSGIScope:
    def __init__(
        self, method="GET", path="/", query_string="", headers=None, proto="http"
    ):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.headers = headers if headers is not None else []
        self.proto = proto
        self.scheme = "http"
        self.http_version = "1.1"
        self.client = ("127.0.0.1", 54321)


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


class NoEncodeStr(str):
    """A string subclass that raises if encode() is called."""

    def encode(self, *args, **kwargs):
        raise AssertionError("str.encode was called on a native-str header!")


def test_rsgi_scope_headers_remain_str():
    """1. test_rsgi_scope_headers_remain_str:
    Scope headers remain Python str in _raw_headers without converting to bytes.
    """
    scope = MockRSGIScope(
        headers=[("Content-Type", "application/json"), ("X-Request-Id", "abc")]
    )
    proto = MockRSGIProtocol()
    req = instantiate_rsgi_request(scope, proto)

    # Force header materialization
    val = req.get_first_header("content-type")
    assert val == "application/json"

    # Assert every stored pair in _raw_headers is (str, str)
    raw_headers = req._raw_headers
    assert len(raw_headers) == 2
    for k, v in raw_headers:
        assert isinstance(k, str), f"Key {k!r} is not str"
        assert isinstance(v, str), f"Value {v!r} is not str"
        assert not isinstance(k, bytes), f"Key {k!r} is bytes"
        assert not isinstance(v, bytes), f"Value {v!r} is bytes"


def test_extract_headers_does_not_encode():
    """2. test_extract_headers_does_not_encode:
    Header extraction MUST NOT call .encode() on scope header names or values.
    """
    scope = MockRSGIScope(
        headers=[
            (NoEncodeStr("Content-Type"), NoEncodeStr("application/json")),
            (NoEncodeStr("X-Request-Id"), NoEncodeStr("abc")),
        ]
    )
    proto = MockRSGIProtocol()
    req = instantiate_rsgi_request(scope, proto)

    # Force extraction/materialization
    val = req.get_first_header("content-type")
    assert val == "application/json"

    raw_headers = req._raw_headers
    assert len(raw_headers) == 2
    for k, v in raw_headers:
        assert isinstance(k, str)
        assert isinstance(v, str)
        assert not isinstance(k, bytes)
        assert not isinstance(v, bytes)


def test_get_first_str_key_does_not_encode():
    """3. test_get_first_str_key_does_not_encode:
    Lookup keys in get_first / get_first_header MUST NOT be encoded to bytes.
    """
    scope = MockRSGIScope(
        headers=[("Content-Type", "application/json"), ("X-Request-Id", "abc")]
    )
    proto = MockRSGIProtocol()
    req = instantiate_rsgi_request(scope, proto)

    lookup_key = NoEncodeStr("content-type")
    # req.get_first_header
    val = req.get_first_header(lookup_key)
    assert val == "application/json"

    # req.headers.get_first
    val2 = req.headers.get_first(lookup_key)
    assert val2 == "application/json"


def test_send_rsgi_response_sync_str_headers():
    """4. test_send_rsgi_response_sync_str_headers:
    Outbound response with str headers produces str names and values without decode.
    """
    resp = Response(
        200,
        [("x-request-id", "req-12345"), ("content-type", "application/json")],
        Content(b"application/json", b'{"ok":true}'),
    )
    proto = MockRSGIProtocol()
    send_rsgi_response_sync(resp, proto)

    assert proto.sent_status == 200
    assert proto.sent_headers is not None

    for name, value in proto.sent_headers:
        assert isinstance(name, str), f"Outbound header name {name!r} is not str"
        assert isinstance(value, str), f"Outbound header value {value!r} is not str"
        assert not isinstance(name, bytes)
        assert not isinstance(value, bytes)

    headers_dict = dict(proto.sent_headers)
    assert headers_dict["x-request-id"] == "req-12345"
    assert headers_dict["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_asgi_bytes_headers_still_work():
    """5. test_asgi_bytes_headers_still_work:
    ASGI scope with [(b"content-type", b"text/plain")] continues to serve properly.
    """
    app = Application()
    received_header = None

    @get("/asgi-test")
    def handler(request):
        nonlocal received_header
        received_header = request.get_first_header(b"content-type")
        return text("asgi ok")

    app.router.add_get("/asgi-test", handler)
    await app.start()

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/asgi-test",
        "raw_path": b"/asgi-test",
        "query_string": b"",
        "headers": [(b"content-type", b"text/plain")],
    }
    response = None

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(msg):
        nonlocal response
        if msg["type"] == "http.response.start":
            response = msg

    await app(scope, receive, send)
    assert response is not None
    assert response["status"] == 200
    assert received_header == b"text/plain"


def test_path_str_not_regressed():
    """6. test_path_str_not_regressed:
    instantiate_rsgi_request sets str path/query; get_match hits static_routes_str.
    """
    scope = MockRSGIScope(method="GET", path="/users/42", query_string="search=hello")
    proto = MockRSGIProtocol()
    req = instantiate_rsgi_request(scope, proto)
    assert isinstance(req.path, str)
    assert req.path == "/users/42"
    assert isinstance(req.query_string, str)
    assert req.query_string == "search=hello"

    app = Application()

    @get("/static-path")
    def handler():
        return text("ok")

    app.router.add_get("/static-path", handler)
    app.router.apply_routes()
    router = app.router
    # Hits static_routes_str on radix tree
    radix = getattr(router, "_radix_router", router)
    tree = radix.trees.get("GET") or radix.trees.get(b"GET")
    assert "/static-path" in tree.static_routes_str
    match = router.get_match_by_method_and_path("GET", "/static-path")
    assert match is not None


@pytest.mark.asyncio
async def test_mount_rsgi_or_check_fails():
    """7. Ticket M: test_mount_rsgi_or_check_fails:
    Mount child app and hit it via RSGI fake protocol, and ensure des check detects mounts.
    """
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    assert hasattr(MountMixin, "__rsgi__")

    parent_app = Application()
    child_app = Application()

    @child_app.router.get("/hello")
    def child_hello():
        return text("child rsgi response")

    parent_app.mount("/sub", child_app)
    await parent_app.start()
    await child_app.start()

    scope = MockRSGIScope(method="GET", path="/sub/hello")
    proto = MockRSGIProtocol()
    await parent_app.__rsgi__(scope, proto)

    assert proto.sent_status == 200
    assert proto.sent_body == b"child rsgi response"

    # Also verify des check detects mounts
    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "app.py"
        app_file.write_text("""
from des import Application
from dreaming_electric_sheep.server.routing import Router
app = Application()
child = Application(router=Router())
app.mount('/sub', child)
""")
        res = subprocess.run(
            [sys.executable, "-m", "dreaming_electric_sheep.cli", "-C", tmpdir, "check", "app:app", "--json"],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        assert "1 mounted apps" in data["mounts"]


def test_ticket_d_grep_gates():
    """8. Ticket D grep gates (CI):
    Validates README first prose sentence, example block, absence of 180k/10-15%,
    and AGENTS.md ordering.
    """
    # 1. README first sentence matches Granian tax / binders / des why; NO HTMX or oha
    with open("README.md", "r", encoding="utf-8") as f:
        prose_line = None
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if (
                "<img" in stripped
                or "<h1" in stripped
                or "</h1>" in stripped
                or "<a" in stripped
                or "---" in stripped
                or stripped == "</p>"
                or stripped == '<p align="center">'
            ):
                continue
            prose_line = stripped
            break

    assert prose_line is not None
    assert "tax" in prose_line.lower() or "granian" in prose_line.lower()
    assert "binders" in prose_line.lower() or "msgspec" in prose_line.lower()
    assert "des why" in prose_line
    assert "htmx" not in prose_line.lower(), "First sentence must not contain HTMX"
    assert "oha" not in prose_line.lower(), "First sentence must not contain oha"

    # 2. README example block contains from des import and msgspec and no fragment(
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()
    example_idx = content.find("## Example")
    features_idx = content.find("## Features")
    assert example_idx != -1 and features_idx != -1
    example_section = content[example_idx:features_idx]
    assert "from des import" in example_section
    assert "msgspec" in example_section
    assert "fragment(" not in example_section

    # 3. No 180k claims in docs/why-des.md or README.md
    with open("docs/why-des.md", "r", encoding="utf-8") as f:
        why_content = f.read()
    assert not re.search(r"180,?000|~180k", why_content)
    assert not re.search(r"180,?000|~180k", content)

    # 4. No 10-15% claims in README.md or docs/why-des.md
    assert not re.search(r"10–15%|10-15%", why_content)
    assert not re.search(r"10–15%|10-15%", content)

    # 5. AGENTS.md mentions -t api before -t fullstack
    with open("AGENTS.md", "r", encoding="utf-8") as f:
        agents_content = f.read()
    api_pos = agents_content.find("-t api")
    fullstack_pos = agents_content.find("-t fullstack")
    assert api_pos != -1 and fullstack_pos != -1
    assert api_pos < fullstack_pos, "-t api must precede -t fullstack in AGENTS.md"
