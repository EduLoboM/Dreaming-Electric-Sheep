import pytest
from rodi import Container

from dreaming_electric_sheep.messages import Request, Response
from dreaming_electric_sheep.server.application import Application
from dreaming_electric_sheep.server.controllers import Controller
from dreaming_electric_sheep.testing import TestClient


class DatabaseService:
    def __init__(self):
        self.connected = True

    def query(self, entity_id: int) -> str:
        return f"Entity-{entity_id}"


class GreeterService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


@pytest.mark.asyncio
async def test_simple_controller_prebound_dispatch():
    app = Application()
    get = app.controllers_router.get
    post = app.controllers_router.post

    class SimpleController(Controller):
        route = "/simple"

        @get("/")
        def index(self):
            return self.text("Simple Index")

        @get("/greet/{name}")
        async def greet(self, name: str):
            return self.text(f"Hi {name}")

        @post("/calculate/{a}/{b}")
        def add(self, a: int, b: int):
            return self.json({"result": int(a) + int(b)})

    await app.start()
    client = TestClient(app)

    # Test 0 extra params
    resp = await client.get("/simple/")
    assert resp.status == 200
    assert await resp.text() == "Simple Index"

    # Test 1 extra param
    resp = await client.get("/simple/greet/Antigravity")
    assert resp.status == 200
    assert await resp.text() == "Hi Antigravity"

    # Test 2 extra params
    resp = await client.post("/simple/calculate/10/25")
    assert resp.status == 200
    assert await resp.json() == {"result": 35}


@pytest.mark.asyncio
async def test_controller_with_injected_dependencies():
    app = Application()
    app.services.add_singleton(DatabaseService)
    app.services.add_transient(GreeterService)
    get = app.controllers_router.get

    class InjectedController(Controller):
        route = "/injected"

        def __init__(self, db: DatabaseService, greeter: GreeterService):
            self.db = db
            self.greeter = greeter

        @get("/{id}")
        def get_by_id(self, id: int):
            entity = self.db.query(int(id))
            greeting = self.greeter.greet(entity)
            return self.text(greeting)

    await app.start()
    client = TestClient(app)

    resp = await client.get("/injected/77")
    assert resp.status == 200
    assert await resp.text() == "Hello, Entity-77!"
