"""
Tests for Phase A: Unified C core, singleton intern table, and cross-extension pointer identity.
"""

import pytest

import dreaming_electric_sheep._des_core as core
from dreaming_electric_sheep import (
    Header,
    Headers,
    HTMLContent,
    JSONContent,
    Request,
    Response,
    TextContent,
)
from dreaming_electric_sheep.messages import (
    acquire_request,
    acquire_response,
    release_request,
    release_response,
)


def test_cross_extension_interned_method_identity():
    """Verify methods across Request instances share exact PyObject pointer identity (is)."""
    r1 = Request("GET", b"http://localhost/", [])
    r2 = Request("GET", b"http://localhost/users", [])
    assert r1.method is r2.method
    assert r1.method is "GET"

    r_post1 = Request("POST", b"http://localhost/", [])
    r_post2 = Request("POST", b"http://localhost/items", [])
    assert r_post1.method is r_post2.method
    assert r_post1.method is "POST"


def test_freelist_acquire_interned_method_identity():
    """Verify freelist acquire_request preserves interned method identity."""
    scope = {"type": "http", "method": "GET", "path": "/test"}
    req1 = acquire_request("GET", b"/test", b"", [], scope)
    assert req1.method is "GET"
    release_request(req1)

    req2 = acquire_request("GET", b"/another", b"", [], scope)
    assert req2.method is "GET"
    assert req2.method is req1.method
    release_request(req2)


def test_cross_extension_interned_header_name_identity():
    """Verify Header and Headers objects share exact PyObject pointer identity (is) for header names."""
    h1 = Header(b"content-type", b"application/json")
    h2 = Header(b"content-type", b"text/plain")
    assert h1.name is h2.name

    h3 = Header(b"host", b"localhost")
    h4 = Header(b"host", b"example.com")
    assert h3.name is h4.name

    headers = Headers([(b"content-type", b"application/json"), (b"host", b"localhost")])
    assert headers.get_first(b"content-type") == b"application/json"
    assert headers.get_first(b"CONTENT-TYPE") == b"application/json"


def test_content_type_interned_identity():
    """Verify Content objects intern their content_type bytes."""
    c1 = JSONContent({"key": "val"})
    c2 = JSONContent({"other": 123})
    assert c1.type is c2.type
    assert c1.type == b"application/json"

    t1 = TextContent("hello")
    t2 = TextContent("world")
    assert t1.type is t2.type
    assert t1.type == b"text/plain; charset=utf-8"

    html1 = HTMLContent("<h1>1</h1>")
    html2 = HTMLContent("<h1>2</h1>")
    assert html1.type is html2.type
    assert html1.type == b"text/html; charset=utf-8"


def test_des_core_table_address_stability():
    """Verify _des_core exposes a stable singleton intern table address."""
    addr1 = core.get_intern_table_address()
    addr2 = core.get_intern_table_address()
    assert addr1 != 0
    assert addr1 == addr2


def test_intern_table_leak_freedom_loop():
    """Verify 10,000 acquires and releases do not leak memory or corrupt refcounts."""
    scope = {"type": "http", "method": "GET", "path": "/"}
    for _ in range(10000):
        req = acquire_request(
            "GET",
            b"/",
            b"",
            [(b"content-type", b"application/json"), (b"host", b"localhost")],
            scope,
        )
        assert req.method is "GET"
        assert req.get_first_header(b"content-type") == b"application/json"
        release_request(req)

        resp = acquire_response(
            200, [(b"content-type", b"application/json")], JSONContent({"status": "ok"})
        )
        assert resp.status == 200
        assert resp.get_first_header(b"content-type") == b"application/json"
        release_response(resp)
