"""
Root module of the framework. This module re-exports the most commonly
used types to reduce the verbosity of the imports statements.
"""

__author__ = (
    "Eduardo Lobo <eduardolobomoreira@tuta.io> (Fork author), "
    "Roberto Prevato <roberto.prevato@gmail.com> (Original BlackSheep author)"
)
__version__ = "1.0.0"

import os
import sys
import ctypes
import importlib
from typing import Any

try:
    _pkg_dir = os.path.dirname(__file__)
    _core_path = None
    for _name in os.listdir(_pkg_dir):
        if _name.startswith("_des_core") and (_name.endswith(".so") or _name.endswith(".pyd")):
            _core_path = os.path.join(_pkg_dir, _name)
            break
    if _core_path and hasattr(ctypes, "RTLD_GLOBAL"):
        ctypes.CDLL(_core_path, mode=ctypes.RTLD_GLOBAL)
    from . import _des_core as _des_core
except Exception:
    _des_core = None

# Core Cython / C extension fast types (loaded eagerly, microsecond cost)
from .contents import Content as Content
from .contents import FileBuffer as FileBuffer
from .contents import FormContent as FormContent
from .contents import FormPart as FormPart
from .contents import HTMLContent as HTMLContent
from .contents import JSONContent as JSONContent
from .contents import MultiPartFormData as MultiPartFormData
from .contents import StreamedContent as StreamedContent
from .contents import TextContent as TextContent
from .contents import parse_www_form as parse_www_form
from .cookies import Cookie as Cookie
from .cookies import CookieSameSiteMode as CookieSameSiteMode
from .cookies import datetime_from_cookie_format as datetime_from_cookie_format
from .cookies import datetime_to_cookie_format as datetime_to_cookie_format
from .cookies import parse_cookie as parse_cookie
from .exceptions import HTTPException as HTTPException
from .exceptions import UnprocessableEntity as UnprocessableEntity
from .core_errors import (
    DesCoreError as DesCoreError,
    MemoryExhaustedError as MemoryExhaustedError,
    ParseError as ParseError,
    SimdUnsupportedError as SimdUnsupportedError,
    InvalidArgumentError as InvalidArgumentError,
)
from .headers import Header as Header
from .headers import Headers as Headers
from .messages import Message as Message
from .messages import Request as Request
from .messages import Response as Response
from .url import URL as URL
from .url import InvalidURL as InvalidURL

# Lazy exports for server, bindings, rendering, and websocket modules (PEP 562)
_LAZY_EXPORTS = {
    # server.application
    "Application": ".server.application",
    "show_warning": ".server.application",
    # server.authorization
    "allow_anonymous": ".server.authorization",
    "auth": ".server.authorization",
    # server.bindings
    "ClientInfo": ".server.bindings",
    "FromBody": ".server.bindings",
    "FromBytes": ".server.bindings",
    "FromCookie": ".server.bindings",
    "FromFiles": ".server.bindings",
    "FromForm": ".server.bindings",
    "FromHeader": ".server.bindings",
    "FromJSON": ".server.bindings",
    "FromQuery": ".server.bindings",
    "FromRoute": ".server.bindings",
    "FromServices": ".server.bindings",
    "FromText": ".server.bindings",
    "FromXML": ".server.bindings",
    "ServerInfo": ".server.bindings",
    # server.responses
    "ContentDispositionType": ".server.responses",
    "FileInput": ".server.responses",
    "accepted": ".server.responses",
    "bad_request": ".server.responses",
    "created": ".server.responses",
    "file": ".server.responses",
    "forbidden": ".server.responses",
    "html": ".server.responses",
    "json": ".server.responses",
    "moved_permanently": ".server.responses",
    "no_content": ".server.responses",
    "not_found": ".server.responses",
    "not_modified": ".server.responses",
    "ok": ".server.responses",
    "permanent_redirect": ".server.responses",
    "pretty_json": ".server.responses",
    "redirect": ".server.responses",
    "see_other": ".server.responses",
    "status_code": ".server.responses",
    "temporary_redirect": ".server.responses",
    "text": ".server.responses",
    "unauthorized": ".server.responses",
    "view": ".server.responses",
    "view_async": ".server.responses",
    # server.routing
    "Route": ".server.routing",
    "RouteException": ".server.routing",
    "RouteNotFound": ".server.routing",
    "Router": ".server.routing",
    "RoutesRegistry": ".server.routing",
    "connect": ".server.routing",
    "delete": ".server.routing",
    "get": ".server.routing",
    "head": ".server.routing",
    "options": ".server.routing",
    "patch": ".server.routing",
    "post": ".server.routing",
    "put": ".server.routing",
    "route": ".server.routing",
    "trace": ".server.routing",
    "ws": ".server.routing",
    # server.websocket
    "WebSocket": ".server.websocket",
    "WebSocketDisconnectError": ".server.websocket",
    "WebSocketError": ".server.websocket",
    # structures
    "Struct": ".structures",
    "struct": ".structures",
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        mod_name = _LAZY_EXPORTS[name]
        mod = importlib.import_module(mod_name, package=__name__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))
