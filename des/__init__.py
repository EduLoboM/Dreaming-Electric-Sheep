"""
Top-level package alias `des` for Dreaming Electric Sheep (`dreaming_electric_sheep`).
"""
import sys
import dreaming_electric_sheep as _des
from dreaming_electric_sheep import *  # noqa: F401, F403
from dreaming_electric_sheep import (
    Application,
    Content,
    Cookie,
    FileBuffer,
    FormContent,
    HTMLContent,
    HTTPException,
    Header,
    Headers,
    JSONContent,
    Message,
    MultiPartFormData,
    Request,
    Response,
    Route,
    Router,
    StreamedContent,
    Struct,
    TextContent,
    URL,
    UnprocessableEntity,
    WebSocket,
    __author__,
    __version__,
    accepted,
    bad_request,
    connect,
    created,
    delete,
    file,
    forbidden,
    get,
    head,
    html,
    json,
    moved_permanently,
    no_content,
    not_found,
    not_modified,
    ok,
    options,
    patch,
    permanent_redirect,
    post,
    pretty_json,
    put,
    redirect,
    route,
    see_other,
    status_code,
    struct,
    temporary_redirect,
    text,
    trace,
    unauthorized,
    view,
    view_async,
    ws,
)


def __getattr__(name: str):
    return getattr(_des, name)


def __dir__():
    return dir(_des)
