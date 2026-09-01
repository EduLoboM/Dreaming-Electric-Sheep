import pytest
from des import (
    Application,
    Request,
    fragment,
    hx_trigger,
    hx_redirect,
    hx_refresh,
    hx_reswap,
    sse_stream,
    ndjson_stream,
)
from dreaming_electric_sheep.contents import TextServerSentEvent
from dreaming_electric_sheep.testing import TestClient


def test_htmx_request_inspection():
    # Non-HTMX request
    req = Request.incoming("GET", b"/", b"", [(b"user-agent", b"pytest")])
    assert req.is_htmx is False
    assert req.htmx_target is None
    assert req.htmx_trigger is None
    assert req.htmx_current_url is None
    assert req.htmx_prompt is None
    assert req.htmx_target_id is None

    # HTMX request with headers
    headers = [
        (b"hx-request", b"true"),
        (b"hx-target", b"#user-profile"),
        (b"hx-trigger", b"save-btn"),
        (b"hx-current-url", b"http://localhost:8000/users/42"),
        (b"hx-prompt", b"Enter your name"),
    ]
    req2 = Request.incoming("POST", b"/users/42", b"", headers)
    assert req2.is_htmx is True
    assert req2.htmx_target == "#user-profile"
    assert req2.htmx_target_id == "user-profile"
    assert req2.htmx_trigger == "save-btn"
    assert req2.htmx_current_url == "http://localhost:8000/users/42"
    assert req2.htmx_prompt == "Enter your name"


def test_htmx_response_helpers():
    # hx_redirect
    res_red = hx_redirect("/dashboard")
    assert res_red.status == 200
    assert res_red.get_first_header(b"hx-redirect") == b"/dashboard"

    # hx_refresh
    res_ref = hx_refresh()
    assert res_ref.status == 200
    assert res_ref.get_first_header(b"hx-refresh") == b"true"

    # hx_reswap
    res_swap = hx_reswap("outerHTML")
    assert res_swap.status == 200
    assert res_swap.get_first_header(b"hx-reswap") == b"outerHTML"

    # hx_trigger with string
    res_trig1 = hx_trigger("itemAdded")
    assert res_trig1.get_first_header(b"hx-trigger") == b"itemAdded"

    # hx_trigger with payload
    res_trig2 = hx_trigger("itemAdded", {"id": 123, "status": "success"})
    assert b'{"itemAdded":{"id":123,"status":"success"}}' in res_trig2.get_first_header(b"hx-trigger")

    # hx_trigger with dict
    res_trig3 = hx_trigger({"itemAdded": 123, "notify": "Saved"})
    assert b'"itemAdded":123' in res_trig3.get_first_header(b"hx-trigger")
    assert b'"notify":"Saved"' in res_trig3.get_first_header(b"hx-trigger")


@pytest.mark.asyncio
async def test_htmx_endpoints_in_app():
    app = Application()

    @app.router.get("/items")
    def get_items(request: Request):
        if request.is_htmx:
            return fragment("<tr><td>Item 1</td></tr>")
        return fragment("<table><tr><td>Item 1</td></tr></table>")

    @app.router.post("/items")
    def create_item():
        resp = fragment("<tr><td>Item 2 (Created)</td></tr>")
        return hx_trigger("itemCreated", {"id": 2}, resp)

    @app.router.get("/refresh-test")
    def refresh_test():
        return hx_refresh()

    @app.router.get("/redirect-test")
    def redirect_test():
        return hx_redirect("/new-location")

    await app.start()
    client = TestClient(app)

    # Regular request
    res = await client.get("/items")
    assert res.status == 200
    assert (await res.text()) == "<table><tr><td>Item 1</td></tr></table>"

    # HTMX request
    res_htmx = await client.get("/items", headers={"HX-Request": "true", "HX-Target": "#items-table"})
    assert res_htmx.status == 200
    assert (await res_htmx.text()) == "<tr><td>Item 1</td></tr>"

    # HTMX creation with trigger
    res_create = await client.post("/items")
    assert res_create.status == 200
    assert (await res_create.text()) == "<tr><td>Item 2 (Created)</td></tr>"
    assert b"itemCreated" in res_create.headers.get_first(b"hx-trigger")

    # Refresh
    res_ref = await client.get("/refresh-test")
    assert res_ref.headers.get_first(b"hx-refresh") == b"true"

    # Redirect
    res_red = await client.get("/redirect-test")
    assert res_red.headers.get_first(b"hx-redirect") == b"/new-location"


@pytest.mark.asyncio
async def test_sse_and_ndjson_streaming():
    app = Application()

    @app.router.get("/events")
    def sse_events():
        async def event_generator():
            yield TextServerSentEvent("status: online", event="ping")
            yield {"msg": "hello", "count": 1}
            yield "raw update"

        return sse_stream(event_generator)

    @app.router.get("/stream-ndjson")
    def ndjson_endpoint():
        async def data_gen():
            yield {"id": 1, "name": "Item A"}
            yield {"id": 2, "name": "Item B"}

        return ndjson_stream(data_gen)

    await app.start()
    client = TestClient(app)

    # Test SSE Stream
    res_sse = await client.get("/events")
    assert res_sse.status == 200
    assert res_sse.headers.get_first(b"content-type") == b"text/event-stream"
    sse_body = await res_sse.text()
    assert "event: ping" in sse_body
    assert "status: online" in sse_body
    assert '{"msg":"hello","count":1}' in sse_body
    assert "raw update" in sse_body

    # Test NDJSON Stream
    res_ndjson = await client.get("/stream-ndjson")
    assert res_ndjson.status == 200
    assert res_ndjson.headers.get_first(b"content-type") == b"application/x-ndjson"
    ndjson_body = await res_ndjson.text()
    lines = [line for line in ndjson_body.strip().split("\n") if line]
    assert len(lines) == 2
    assert '"Item A"' in lines[0]
    assert '"Item B"' in lines[1]
