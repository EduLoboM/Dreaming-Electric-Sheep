"""
Unit tests for synchronous handler wrappers (Ticket B).
Verifies that sync `def` handlers with sync binders stay synchronous,
are not wrapped in `async def`, and execute without coroutine overhead.
"""

import inspect

import pytest

from des import Application, Request, Response, get, post
from dreaming_electric_sheep.structures import Struct


class UserPayload(Struct):
    username: str


@pytest.mark.asyncio
async def test_sync_handler_zero_args_stays_sync():
    app = Application()

    @get("/sync-zero")
    def sync_zero():
        return {"status": "sync_ok"}

    app.router.add_get("/sync-zero", sync_zero)
    await app.start()

    route = app.router.get_matching_route(b"GET", b"/sync-zero")
    assert route is not None

    # Handler MUST NOT be a coroutine function
    assert not inspect.iscoroutinefunction(
        route.handler
    ), "Sync handler must not be wrapped in async def"

    # Calling handler directly executes synchronously and returns a Response
    req = Request.incoming("GET", b"/sync-zero", b"", [])
    res = route.handler(req)
    assert isinstance(res, Response), f"Expected Response instance, got {type(res)}"
    assert res.status == 200


@pytest.mark.asyncio
async def test_sync_handler_with_request_arg_stays_sync():
    app = Application()

    @get("/sync-req")
    def sync_req(request: Request):
        return {"path": request.path}

    app.router.add_get("/sync-req", sync_req)
    await app.start()

    route = app.router.get_matching_route(b"GET", b"/sync-req")
    assert route is not None
    assert not inspect.iscoroutinefunction(route.handler)

    req = Request.incoming("GET", b"/sync-req", b"", [])
    res = route.handler(req)
    assert isinstance(res, Response)
    assert res.status == 200


@pytest.mark.asyncio
async def test_sync_handler_with_route_binder_stays_sync():
    app = Application()

    @get("/items/{item_id}")
    def get_item(item_id: int):
        return {"item_id": item_id}

    app.router.add_get("/items/{item_id}", get_item)
    await app.start()

    route_match = app.router.get_matching_route(b"GET", b"/items/42")
    assert route_match is not None
    assert not inspect.iscoroutinefunction(route_match.handler)

    req = Request.incoming("GET", b"/items/42", b"", [])
    req.route_values = getattr(route_match, "values", {"item_id": "42"})
    res = route_match.handler(req)
    assert isinstance(res, Response)
    assert res.status == 200


@pytest.mark.asyncio
async def test_sync_handler_with_query_binder_stays_sync():
    app = Application()

    @get("/search")
    def search(q: str):
        return {"query": q}

    app.router.add_get("/search", search)
    await app.start()

    route = app.router.get_matching_route(b"GET", b"/search")
    assert route is not None
    assert not inspect.iscoroutinefunction(route.handler)

    req = Request.incoming("GET", b"/search", b"q=neural_networks", [])
    res = route.handler(req)
    assert isinstance(res, Response)
    assert res.status == 200


@pytest.mark.asyncio
async def test_async_handler_remains_async():
    app = Application()

    @get("/async-handler")
    async def async_fn():
        return {"status": "async_ok"}

    app.router.add_get("/async-handler", async_fn)
    await app.start()

    route = app.router.get_matching_route(b"GET", b"/async-handler")
    assert route is not None
    assert inspect.iscoroutinefunction(route.handler)


@pytest.mark.asyncio
async def test_sync_handler_with_async_body_binder_is_async_wrapped():
    app = Application()

    @post("/users")
    def create_user(user: UserPayload):
        return {"created": user.username}

    app.router.add_post("/users", create_user)
    await app.start()

    route = app.router.get_matching_route(b"POST", b"/users")
    assert route is not None
    # Because reading request body stream is asynchronous, body binder forces async wrapper
    assert inspect.iscoroutinefunction(route.handler)
