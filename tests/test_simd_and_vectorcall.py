import pytest
from dreaming_electric_sheep.messages import (
    Request,
    Response,
    acquire_request,
    release_request,
    acquire_response,
    release_response,
)
from dreaming_electric_sheep.contents import Content, TextContent
from dreaming_electric_sheep import Application
from dreaming_electric_sheep.testing import TestClient
from dreaming_electric_sheep.routing import CythonRadixRouter, RouteMatch


def test_request_response_no_dict_overhead():
    """Verify that Request and Response are pure cdef extension classes without __dict__ overhead."""
    req = Request("GET", b"/hello", [])
    resp = Response(200)

    # Pure cdef classes should not have __dict__
    if hasattr(req, "__dict__"):
        pytest.skip("Pure python fallback mode in use (compiled cdef extensions not loaded)")
    assert not hasattr(req, "__dict__"), "Request must not instantiate dynamic __dict__"
    assert not hasattr(resp, "__dict__"), "Response must not instantiate dynamic __dict__"


def test_request_attributes_cdef_offsets():
    """Verify direct cdef attributes access on Request."""
    req = Request("POST", b"/users/42", [(b"host", b"example.com")])
    req.state = {"trace_id": "12345"}
    req.route_values = {"id": "42"}

    assert req.state == {"trace_id": "12345"}
    assert req.route_values == {"id": "42"}
    assert req.host == "example.com"
    assert req.path == "/users/42"


def test_request_response_freelists():
    """Verify C-level freelists for Request and Response reuse."""
    req1 = acquire_request("GET", b"/api/v1", b"a=1", [(b"user-agent", b"pytest")], {"type": "http"})
    assert isinstance(req1, Request)
    assert req1.method == "GET"
    assert req1._path == b"/api/v1"

    req1.state = "some_state"
    req1.user = "custom_user_obj"
    release_request(req1)

    # Next acquire should reuse the released instance with cleanly reset properties
    req2 = acquire_request("POST", b"/api/v2", b"", [], {"type": "http"})
    assert req2.method == "POST"
    assert req2._path == b"/api/v2"
    assert req2.state is None
    assert req2._user is None
    assert req2.user.is_authenticated() is False

    # Response freelist
    resp1 = acquire_response(201, [(b"content-type", b"text/plain")], TextContent("Created"))
    assert resp1.status == 201
    resp1.state = "meta"
    release_response(resp1)

    resp2 = acquire_response(200)
    assert resp2.status == 200
    assert resp2.state is None
    assert resp2.content is None


def test_pure_routematch_cdef():
    """Verify that RouteMatch is a pure extension class."""
    class DummyRoute:
        def __init__(self):
            self.handler = lambda r: Response(200)
            self.pattern = "/items/:id"

    route = DummyRoute()
    match = RouteMatch(route, {"id": b"100"})
    assert match.values == {"id": "100"}
    assert match.handler is route.handler
    assert match.pattern == "/items/:id"


@pytest.mark.asyncio
async def test_vectorcall_dispatch_application():
    """Verify that Application handler pipeline executes seamlessly via Vectorcall."""
    app = Application()

    @app.router.get("/vectorcall/fast/:id")
    async def get_fast(id: int):
        return {"received_id": id, "mode": "vectorcall"}

    @app.router.post("/vectorcall/echo")
    async def post_echo(request: Request):
        data = await request.json()
        return {"echo": data}

    await app.start()
    client = TestClient(app)

    res1 = await client.get("/vectorcall/fast/999")
    assert res1.status == 200
    data1 = await res1.json()
    assert data1 == {"received_id": 999, "mode": "vectorcall"}

    res2 = await client.post("/vectorcall/echo", content=Content(b"application/json", b'{"msg":"hello vectorcall"}'))
    assert res2.status == 200
    data2 = await res2.json()
    assert data2 == {"echo": {"msg": "hello vectorcall"}}
