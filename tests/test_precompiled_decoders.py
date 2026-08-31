from dataclasses import dataclass
from typing import List
from uuid import UUID, uuid4

import msgspec
import pytest

from dreaming_electric_sheep.contents import Content
from dreaming_electric_sheep.messages import Request, Response
from dreaming_electric_sheep.server.application import Application
from dreaming_electric_sheep.server.bindings import (
    FromJSON,
    JSONBinder,
    get_precompiled_decoder,
    get_precompiled_encoder,
)
from dreaming_electric_sheep.testing import TestClient
from dreaming_electric_sheep.testing.helpers import get_example_scope
from dreaming_electric_sheep.testing.messages import MockReceive, MockSend


class UserStruct(msgspec.Struct):
    id: int
    name: str
    is_admin: bool = False


@dataclass
class ItemData:
    sku: str
    price: float


def test_get_precompiled_decoder_caching():
    # Calling get_precompiled_decoder multiple times for the same type returns the exact same cached instance
    dec1 = get_precompiled_decoder(UserStruct)
    dec2 = get_precompiled_decoder(UserStruct)
    assert dec1 is dec2

    dec_dict1 = get_precompiled_decoder(dict)
    dec_dict2 = get_precompiled_decoder(dict)
    assert dec_dict1 is dec_dict2


def test_get_precompiled_encoder_caching():
    enc1 = get_precompiled_encoder()
    enc2 = get_precompiled_encoder()
    assert enc1 is enc2


@pytest.mark.asyncio
async def test_json_binder_precompiled_decoding():
    binder = JSONBinder(UserStruct)
    payload = b'{"id": 123, "name": "Alice", "is_admin": true}'
    request = Request(
        "POST", b"/users", [(b"content-type", b"application/json")]
    ).with_content(Content(b"application/json", payload))

    user = await binder.get_value(request)
    assert isinstance(user, UserStruct)
    assert user.id == 123
    assert user.name == "Alice"
    assert user.is_admin is True


@pytest.mark.asyncio
async def test_json_binder_dataclass_and_uuid_decoding():
    uid = uuid4()
    binder = JSONBinder(UUID)
    request = Request(
        "POST", b"/uuid", [(b"content-type", b"application/json")]
    ).with_content(Content(b"application/json", f'"{str(uid)}"'.encode("utf8")))

    result_uuid = await binder.get_value(request)
    assert result_uuid == uid


@pytest.mark.asyncio
async def test_endpoint_typed_return_startup_caching():
    app = Application()

    @app.router.get("/user")
    async def get_user() -> UserStruct:
        return UserStruct(id=1, name="CachedUser", is_admin=True)

    @app.router.get("/items")
    def get_items() -> List[ItemData]:
        return [ItemData(sku="A1", price=9.99), ItemData(sku="B2", price=19.99)]

    # Start application to trigger normalization and startup caching
    await app.start()

    # Verify route handler return_type attribute was assigned at startup
    route_user = app.router.get_matching_route("GET", "/user")
    assert route_user is not None
    assert getattr(route_user.handler, "return_type", None) is UserStruct

    # Verify requests execute and serialize directly through pre-compiled encoders
    client = TestClient(app)
    resp = await client.get("/user")
    assert resp.status == 200
    assert resp.content_type() == b"application/json"
    data = await resp.json()
    assert data == {"id": 1, "name": "CachedUser", "is_admin": True}

    resp = await client.get("/items")
    assert resp.status == 200
    items_data = await resp.json()
    assert items_data == [
        {"sku": "A1", "price": 9.99},
        {"sku": "B2", "price": 19.99},
    ]
