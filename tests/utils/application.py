from essentials.meta import deprecated

from dreaming_electric_sheep.messages import Request, Response
from dreaming_electric_sheep.server import Application


class FakeApplication(Application):
    """Application class used for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_start: bool = True
        self.request: Request | None = None
        self.response: Response | None = None
        self.register_default_di_types()

    @deprecated(
        "This function is not needed anymore, and will be removed. Rely instead on "
        "await app.start() or the automatic start happening on await app(...)."
    )
    def setup_controllers(self):
        pass

    async def handle(self, request):
        res = super().handle(request)
        if not isinstance(res, Response):
            response = await res
        else:
            response = res
        self.request = request
        self.response = response
        return response

    async def __call__(self, scope, receive, send):
        if not self.started and self.auto_start:
            await self.start()
        return await super().__call__(scope, receive, send)
