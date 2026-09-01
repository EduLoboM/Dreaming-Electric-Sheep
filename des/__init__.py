"""
Top-level package alias `des` for Dreaming Electric Sheep (`dreaming_electric_sheep`).
"""

# flake8: noqa
import dreaming_electric_sheep as _des
from dreaming_electric_sheep import *  # noqa: F401, F403
from dreaming_electric_sheep import (
    URL,
    Application,
    Content,
    Cookie,
    FileBuffer,
    FormContent,
    Header,
    Headers,
    HTMLContent,
    HTTPException,
    JinjaRenderer,
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
    UnprocessableEntity,
    WebSocket,
    __author__,
    __version__,
    accepted,
    acquire_response,
    bad_request,
    connect,
    created,
    delete,
    file,
    forbidden,
    fragment,
    get,
    head,
    html,
    html_settings,
    hx_redirect,
    hx_refresh,
    hx_reswap,
    hx_trigger,
    json,
    json_settings,
    moved_permanently,
    ndjson_stream,
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
    release_response,
    render,
    render_template,
    route,
    see_other,
    sse_stream,
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
