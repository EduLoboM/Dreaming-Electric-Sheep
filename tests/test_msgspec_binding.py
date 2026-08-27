from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import msgspec
import pytest
from pydantic import BaseModel

from dreaming_electric_sheep import Application, FromJSON, post
from dreaming_electric_sheep.contents import Content, JSONContent
from dreaming_electric_sheep.messages import Request
from dreaming_electric_sheep.testing import TestClient


@dataclass
class ItemDataClass:
    name: str
    price: float
    tags: Optional[List[str]] = None


class ItemStruct(msgspec.Struct):
    title: str
    count: int


class ItemPydantic(BaseModel):
    label: str
    active: bool


@dataclass
class UserWithUUID:
    id: UUID
    username: str


@dataclass
class NestedProfile:
    bio: str
    age: int


@dataclass
class UserAccount:
    name: str
    profile: NestedProfile


@pytest.mark.asyncio
async def test_msgspec_binding_dataclass():
    app = Application()

    @post("/items")
    async def create_item(item: ItemDataClass):
        assert isinstance(item, ItemDataClass)
        return {"name": item.name, "price": item.price, "tags": item.tags}

    app.router.add_post("/items", create_item)
    await app.start()
    client = TestClient(app)

    # 1. Valid payload
    response = await client.post(
        "/items",
        content=JSONContent({"name": "apple", "price": 1.99, "tags": ["fruit", "red"]}),
    )
    assert response.status == 200
    data = await response.json()
    assert data == {"name": "apple", "price": 1.99, "tags": ["fruit", "red"]}

    # 2. Schema validation error (invalid price type) -> HTTP 422
    response = await client.post(
        "/items",
        content=JSONContent({"name": "apple", "price": "not_a_float"}),
    )
    assert response.status == 422
    err = await response.json()
    assert "error" in err or "Validation error" in str(err)

    # 3. Missing required field -> HTTP 422
    response = await client.post(
        "/items",
        content=JSONContent({"name": "apple"}),
    )
    assert response.status == 422

    # 4. Malformed JSON syntax -> HTTP 400
    response = await client.post(
        "/items",
        content=Content(b"application/json", b"{\"name\": broken json"),
    )
    assert response.status == 400


@pytest.mark.asyncio
async def test_msgspec_binding_struct():
    app = Application()

    @post("/struct")
    async def create_struct(data: FromJSON[ItemStruct]):
        item = data.value
        assert isinstance(item, ItemStruct)
        return {"title": item.title, "count": item.count}

    app.router.add_post("/struct", create_struct)
    await app.start()
    client = TestClient(app)

    # 1. Valid
    response = await client.post(
        "/struct",
        content=JSONContent({"title": "inventory", "count": 42}),
    )
    assert response.status == 200
    res = await response.json()
    assert res == {"title": "inventory", "count": 42}

    # 2. Invalid field type -> HTTP 422
    response = await client.post(
        "/struct",
        content=JSONContent({"title": "inventory", "count": "invalid"}),
    )
    assert response.status == 422

    # 3. Malformed JSON -> HTTP 400
    response = await client.post(
        "/struct",
        content=Content(b"application/json", b"{bad_json"),
    )
    assert response.status == 400


@pytest.mark.asyncio
async def test_msgspec_binding_pydantic():
    app = Application()

    @post("/pydantic")
    async def handle_pydantic(item: ItemPydantic):
        assert isinstance(item, ItemPydantic)
        return {"label": item.label, "active": item.active}

    app.router.add_post("/pydantic", handle_pydantic)
    await app.start()
    client = TestClient(app)

    response = await client.post(
        "/pydantic",
        content=JSONContent({"label": "test", "active": True}),
    )
    assert response.status == 200
    res = await response.json()
    assert res == {"label": "test", "active": True}

    # Validation failure -> HTTP 422
    response = await client.post(
        "/pydantic",
        content=JSONContent({"active": True}),
    )
    assert response.status == 422


@pytest.mark.asyncio
async def test_application_custom_dec_hook():
    class CustomTimestamp:
        def __init__(self, value: int):
            self.value = value

    @dataclass
    class Event:
        name: str
        ts: CustomTimestamp

    def custom_dec_hook(type, obj):
        if type is CustomTimestamp:
            return CustomTimestamp(int(obj))
        return None

    app = Application(dec_hook=custom_dec_hook)

    @post("/event")
    async def handle_event(event: Event):
        assert isinstance(event.ts, CustomTimestamp)
        return {"name": event.name, "ts": event.ts.value}

    app.router.add_post("/event", handle_event)
    await app.start()
    client = TestClient(app)

    response = await client.post(
        "/event",
        content=JSONContent({"name": "login", "ts": 1700000000}),
    )
    assert response.status == 200
    res = await response.json()
    assert res == {"name": "login", "ts": 1700000000}


@pytest.mark.asyncio
async def test_msgspec_binding_list_of_models():
    app = Application()

    @post("/items-bulk")
    async def create_items_bulk(items: List[ItemDataClass]):
        assert all(isinstance(item, ItemDataClass) for item in items)
        return {"count": len(items), "total_price": sum(item.price for item in items)}

    app.router.add_post("/items-bulk", create_items_bulk)
    await app.start()
    client = TestClient(app)

    response = await client.post(
        "/items-bulk",
        content=JSONContent([
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
        ]),
    )
    assert response.status == 200
    res = await response.json()
    assert res == {"count": 2, "total_price": 30.0}

    # Validation error in one list item -> HTTP 422
    response = await client.post(
        "/items-bulk",
        content=JSONContent([
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": "invalid"},
        ]),
    )
    assert response.status == 422


@pytest.mark.asyncio
async def test_msgspec_uuid_support():
    app = Application()

    @post("/user")
    async def handle_user(user: UserWithUUID):
        assert isinstance(user.id, UUID)
        return {"id": str(user.id), "username": user.username}

    app.router.add_post("/user", handle_user)
    await app.start()
    client = TestClient(app)

    uid = uuid4()
    response = await client.post(
        "/user",
        content=JSONContent({"id": str(uid), "username": "alice"}),
    )
    assert response.status == 200
    res = await response.json()
    assert res == {"id": str(uid), "username": "alice"}


@pytest.mark.asyncio
async def test_msgspec_nested_models():
    app = Application()

    @post("/account")
    async def handle_account(acc: UserAccount):
        assert isinstance(acc.profile, NestedProfile)
        return {"name": acc.name, "bio": acc.profile.bio, "age": acc.profile.age}

    app.router.add_post("/account", handle_account)
    await app.start()
    client = TestClient(app)

    response = await client.post(
        "/account",
        content=JSONContent({"name": "bob", "profile": {"bio": "developer", "age": 30}}),
    )
    assert response.status == 200
    res = await response.json()
    assert res == {"name": "bob", "bio": "developer", "age": 30}

    # Nested type validation error -> HTTP 422
    response = await client.post(
        "/account",
        content=JSONContent({"name": "bob", "profile": {"bio": "developer", "age": "not_an_int"}}),
    )
    assert response.status == 422


@pytest.mark.asyncio
async def test_read_raw_buffer_protocol():
    req = Request.incoming("POST", b"/test", b"", [(b"content-type", b"application/json")])
    req.content = Content(b"application/json", b'{"key": "value"}')

    raw = await req.read_raw()
    assert isinstance(raw, (bytes, bytearray, memoryview))
    # Test that msgspec can directly decode this buffer
    decoded = msgspec.json.decode(raw)
    assert decoded == {"key": "value"}


@pytest.mark.asyncio
async def test_frozen_struct_base_class():
    from dreaming_electric_sheep import Struct

    class Product(Struct):
        sku: str
        qty: int

    prod = Product(sku="ABC-123", qty=10)
    assert prod.sku == "ABC-123"
    assert prod.qty == 10

    # Verify frozen behavior (immutability)
    with pytest.raises(AttributeError):
        prod.qty = 20  # type: ignore

    # Verify hashability
    prod_set = {prod}
    assert prod in prod_set

    # Test route binding with frozen Struct
    app = Application()

    @post("/product")
    async def create_product(product: Product):
        assert isinstance(product, Product)
        return {"sku": product.sku, "qty": product.qty}

    app.router.add_post("/product", create_product)
    await app.start()
    client = TestClient(app)

    res = await client.post("/product", content=JSONContent({"sku": "XYZ-999", "qty": 5}))
    assert res.status == 200
    assert (await res.json()) == {"sku": "XYZ-999", "qty": 5}


def test_gc_tuning_configuration():
    import gc

    app = Application(optimize_gc=True, gc_thresholds=(60000, 15, 15))
    assert app.optimize_gc is True
    assert app.gc_thresholds == (60000, 15, 15)
    assert gc.get_threshold() == (60000, 15, 15)


@pytest.mark.asyncio
async def test_read_detached_and_detach_raw():
    req = Request.incoming("POST", b"/test", b"", [(b"content-type", b"application/json")])
    req.content = Content(b"application/json", b'{"detached": true}')

    detached = await req.read_detached()
    assert isinstance(detached, bytes)
    assert detached == b'{"detached": true}'

    sync_detached = req.detach_raw()
    assert isinstance(sync_detached, bytes)
    assert sync_detached == b'{"detached": true}'

