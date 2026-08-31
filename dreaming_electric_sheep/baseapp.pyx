# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
# cython: language_level=3
# Copyright (C) 2018-present Roberto Prevato and Dreaming Electric Sheep contributors
#
# This module is part of Dreaming Electric Sheep (derived from BlackSheep)
# and is released under the MIT License https://opensource.org/licenses/MIT

import http
import inspect
import logging
from collections import UserDict

from cpython.object cimport PyObject

from .contents cimport Content, TextContent
from .exceptions cimport (
    BadRequest,
    HTTPException,
    InternalServerError,
    InvalidExceptionHandler,
    UnprocessableEntity,
)
from .messages cimport Request, Response

import msgspec
from .utils import get_class_instance_hierarchy

cdef extern from "Python.h":
    object PyObject_Vectorcall(object callable, const PyObject *const *args, size_t nargsf, PyObject *kwnames)
    bint PyCoro_CheckExact(PyObject *p)


cdef inline object vectorcall_1(object callable, object arg0):
    cdef PyObject* args[1]
    args[0] = <PyObject*>arg0
    return PyObject_Vectorcall(callable, args, 1, NULL)


cdef inline object vectorcall_2(object callable, object arg0, object arg1):
    cdef PyObject* args[2]
    args[0] = <PyObject*>arg0
    args[1] = <PyObject*>arg1
    return PyObject_Vectorcall(callable, args, 2, NULL)


cdef inline object vectorcall_3(object callable, object arg0, object arg1, object arg2):
    cdef PyObject* args[3]
    args[0] = <PyObject*>arg0
    args[1] = <PyObject*>arg1
    args[2] = <PyObject*>arg2
    return PyObject_Vectorcall(callable, args, 3, NULL)


# Better support for Pydantic
try:
    from pydantic import ValidationError
except ImportError:
    ValidationError = None


class ExceptionHandlersDict(UserDict):

    def __setitem__(self, key, item) -> None:
        if not inspect.iscoroutinefunction(item):
            raise InvalidExceptionHandler()
        signature = inspect.Signature.from_callable(item)
        if len(signature.parameters) != 3 and not any(
            param
            for param in signature.parameters
            if signature.parameters[param].kind == 2
        ):
            raise InvalidExceptionHandler()
        return super().__setitem__(key, item)


async def handle_not_found(app, Request request, HTTPException http_exception):
    """Default Not Found handler, returns a simple 404 response."""
    return Response(404, content=TextContent("Resource not found"))


async def handle_internal_server_error(app, Request request, Exception exception):
    """Default Internal Server Error handler, returns a simple 500 response."""
    # Intentionally without details!
    return Response(500, content=TextContent("Internal Server Error"))


async def handle_bad_request(app, Request request, HTTPException http_exception):
    # supports for pydantic ValidationError with json() method
    if http_exception.__context__ is not None and callable(getattr(http_exception.__context__, "json", None)):
        return Response(http_exception.status, content=Content(b"application/json", http_exception.__context__.json().encode("utf8")))

    return Response(400, content=TextContent(f'Bad Request: {str(http_exception)}'))


cdef dict _format_validation_details(object details, object default_msg=None):
    cdef list loc
    cdef str msg, msg_clean, path, t
    cdef list tokens
    import re
    if isinstance(details, dict):
        if "detail" in details:
            return details
        if "loc" in details and "msg" in details:
            return {"detail": [details]}
        return {"detail": [{"loc": ["body"], "msg": str(details), "type": "validation_error"}]}
    elif isinstance(details, list):
        if details and isinstance(details[0], dict) and "loc" in details[0]:
            return {"detail": details}
        return {"detail": [{"loc": ["body"], "msg": str(item), "type": "validation_error"} for item in details]}
    elif isinstance(details, str):
        msg = str(details)
        loc = ["body"]
        if " - at `" in msg:
            msg_clean, path = msg.rsplit(" - at `", 1)
            path = path.rstrip("`")
            if path.startswith("$"):
                path = path[1:]
            if path.startswith("."):
                path = path[1:]
            if path:
                tokens = re.findall(r"[^.\[\]]+", path)
                for t in tokens:
                    if t.isdigit():
                        loc.append(int(t))
                    else:
                        loc.append(t)
            msg = msg_clean
        return {"detail": [{"loc": loc, "msg": msg, "type": "validation_error"}]}
    return {"detail": [{"loc": ["body"], "msg": str(default_msg or "Validation error"), "type": "validation_error"}]}


async def handle_unprocessable_entity(app, Request request, HTTPException http_exception):
    """Default 422 Unprocessable Entity handler with FastAPI-compatible structured validation error details."""
    cdef object details = getattr(http_exception, "details", None)
    cdef dict formatted
    cdef bytes body
    if details is not None:
        formatted = _format_validation_details(details, getattr(http_exception, "message", None))
    else:
        formatted = _format_validation_details(getattr(http_exception, "message", None) or "Unprocessable entity")
    body = msgspec.json.encode(formatted)
    return Response(422, content=Content(b"application/json", body))


async def _default_pydantic_validation_error_handler(app, Request request, Exception error):
    return Response(400, content=Content(b"application/json", error.json(indent=4).encode("utf-8")))


async def common_http_exception_handler(app, Request request, HTTPException http_exception):
    return Response(http_exception.status, content=TextContent(http.HTTPStatus(http_exception.status).phrase))


def get_logger():
    logger = logging.getLogger("dreaming_electric_sheep.server")
    logger.setLevel(logging.INFO)
    return logger


cdef class BaseApplication:

    def __init__(self, bint show_error_details, object router):
        self.router = router
        self.exceptions_handlers = self.init_exceptions_handlers()
        self.show_error_details = show_error_details
        self.logger = get_logger()

    def init_exceptions_handlers(self):
        default_handlers = ExceptionHandlersDict({
            404: handle_not_found,
            400: handle_bad_request,
            422: handle_unprocessable_entity,
            UnprocessableEntity: handle_unprocessable_entity,
        })
        if ValidationError is not None:
            default_handlers[ValidationError] = _default_pydantic_validation_error_handler
        return default_handlers

    async def log_unhandled_exc(self, request, exc):
        self.logger.error(
            "Unhandled exception - \"%s %s\"",
            request.method,
            request.url.value.decode(),
            exc_info=exc
        )

    async def log_handled_exc(self, request, exc):
        if isinstance(exc, HTTPException):
            self.logger.info(
                "HTTP %s - \"%s %s\". %s",
                exc.status,
                request.method,
                request.url.value.decode(),
                str(exc)
            )
        else:
            self.logger.info(
                "Handled error: \"%s %s\". %s",
                request.method,
                request.url.value.decode(),
                str(exc)
            )

    cpdef object handle(self, Request request):
        """
        Main request handler dispatch. Sync handlers execute directly at C-level
        without allocating any asyncio Task or coroutine frames. Async handlers
        delegate to _handle_coro.
        """
        cdef object route
        cdef object res

        route = self.router.get_match(request)

        if not route:
            # Main router fallback
            return Response(404)

        request.route_values = route.values
        try:
            res = vectorcall_1(route.handler, request)
        except Exception as exc:
            return self.handle_request_handler_exception(request, exc)

        # Fast path: sync handler returned Response directly
        if isinstance(res, Response):
            return res
        elif res is None:
            return Response(204)
        elif PyCoro_CheckExact(<PyObject*>res) or inspect.isawaitable(res):
            # Async path: coroutine handler, delegate to async helper
            return self._handle_coro(request, res)
        else:
            return res

    async def _handle_coro(self, Request request, object coro):
        cdef Response response
        try:
            response = await coro
        except Exception as exc:
            response = await self.handle_request_handler_exception(request, exc)
        return response or Response(204)

    async def handle_request_handler_exception(self, request, exc):
        if isinstance(exc, HTTPException):
            await self.log_handled_exc(request, exc)
            return await self.handle_http_exception(request, exc)

        if self.is_handled_exception(exc):
            await self.log_handled_exc(request, exc)
        else:
            await self.log_unhandled_exc(request, exc)

        return await self.handle_exception(request, exc)

    cpdef object get_http_exception_handler(self, HTTPException http_exception):
        # Try getting HTTP exception handler by type first, supporting
        # base classes up to a certain point (HTTPException)
        handler = self.get_exception_handler(http_exception, stop_at=HTTPException)
        if handler:
            return handler
        # Try getting HTTP exception handler by HTTP error status code
        return self.exceptions_handlers.get(
            http_exception.status, common_http_exception_handler
        )

    cdef bint is_handled_exception(self, Exception exception):
        for class_type in get_class_instance_hierarchy(exception):
            if class_type in self.exceptions_handlers:
                return True
        return False

    cdef object get_exception_handler(self, Exception exception, type stop_at):
        for class_type in get_class_instance_hierarchy(exception):
            if stop_at is not None and stop_at is class_type:
                return None
            if class_type in self.exceptions_handlers:
                return self.exceptions_handlers[class_type]

        return None

    async def handle_internal_server_error(self, Request request, Exception exc):
        """
        Handle an unhandled exception. If an exception handler is defined for
        InternalServerError or status 500, it is used.
        """
        if self.show_error_details:
            return self.server_error_details_handler.produce_response(request, exc)

        # We want to hide exception details, and possibly use a user-defined
        # handler for this.
        error = InternalServerError(exc)
        internal_server_error_handler = self.get_http_exception_handler(error)

        try:
            return await vectorcall_3(internal_server_error_handler, self, request, error)
        except Exception:
            self.logger.exception(
                "An exception occurred while trying to apply the configured "
                "Internal Server Error handler!"
            )
        return Response(500, content=TextContent("Internal Server Error"))

    async def _apply_exception_handler(self, Request request, Exception exc, object exception_handler):
        try:
            return await vectorcall_3(exception_handler, self, request, exc)
        except Exception as server_ex:
            # If the exception happens in the user-defined exception handler,
            # we need to fallback to the default handlers.
            self.logger.error("Unhandled exception in exception_handler: %s", exception_handler.__name__)
            if self.show_error_details:
                return self.server_error_details_handler.produce_response(request, exc)

            return await handle_internal_server_error(self, request, server_ex)

    async def handle_http_exception(self, Request request, HTTPException http_exception):
        exception_handler = self.get_http_exception_handler(http_exception)
        if exception_handler:
            return await self._apply_exception_handler(request, http_exception, exception_handler)

        return await self.handle_exception(request, http_exception)

    async def handle_exception(self, request, exc):
        exception_handler = self.get_exception_handler(exc, None)
        if exception_handler:
            return await self._apply_exception_handler(request, exc, exception_handler)

        return await self.handle_internal_server_error(request, exc)
