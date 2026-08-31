import logging
from typing import Awaitable, Callable, Type, TypeVar

from dreaming_electric_sheep.exceptions import HTTPException
from dreaming_electric_sheep.messages import Request, Response
from dreaming_electric_sheep.server.application import Application
from dreaming_electric_sheep.server.routing import RouteMatch, Router

ExcT = TypeVar("ExcT", bound=Exception)

ExceptionHandlersType = dict[
    int | Type[Exception],
    Callable[[Application, Request, ExcT], Awaitable[Response]],
]

class BaseApplication:
    def __init__(self, show_error_details: bool, router: Router):
        self.router = router
        self.exceptions_handlers = self.init_exceptions_handlers()
        self.show_error_details = show_error_details
        self.logger: logging.Logger

    def init_exceptions_handlers(self) -> ExceptionHandlersType: ...
    def handle(self, request: Request) -> Response | Awaitable[Response]: ...
    async def handle_internal_server_error(
        self, request: Request, exc: Exception
    ) -> Response: ...
    async def handle_http_exception(
        self, request: Request, http_exception: HTTPException
    ) -> Response: ...
    async def handle_exception(self, request: Request, exc: Exception) -> Response: ...
    async def handle_request_handler_exception(
        self, request: Request, exc: Exception
    ) -> Response: ...
    def get_route_match(self, request: Request) -> RouteMatch | None: ...
    def get_http_exception_handler(
        self, exc: HTTPException
    ) -> (
        Callable[[Application, Request, HTTPException], Awaitable[Response]] | None
    ): ...

def get_logger() -> logging.Logger: ...
async def handle_not_found(
    app: BaseApplication, request: Request, http_exception: HTTPException
) -> Response: ...
async def handle_internal_server_error(
    app: BaseApplication, request: Request, exception: Exception
) -> Response: ...
