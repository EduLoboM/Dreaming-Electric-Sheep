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
import re

from .contents cimport Content, StreamedContent, RSGIContent, ServerSentEvent
from .cookies cimport Cookie, write_cookie_for_response
from .messages cimport Request, Response, acquire_request, release_request, release_response
from .url cimport URL

from cpython.object cimport PyObject
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_GET_SIZE, PyBytes_CheckExact
from cpython.unicode cimport (
    PyUnicode_CheckExact,
    PyUnicode_AsUTF8String,
    PyUnicode_AsLatin1String,
)

# Caches for inbound RSGI
cdef dict _KNOWN_HEADERS = {
    "host": b"host",
    "user-agent": b"user-agent",
    "accept": b"accept",
    "accept-encoding": b"accept-encoding",
    "accept-language": b"accept-language",
    "content-type": b"content-type",
    "content-length": b"content-length",
    "connection": b"connection",
    "cookie": b"cookie",
    "authorization": b"authorization",
    "origin": b"origin",
    "referer": b"referer",
    "cache-control": b"cache-control",
    "pragma": b"pragma",
    "upgrade-insecure-requests": b"upgrade-insecure-requests",
    "sec-ch-ua": b"sec-ch-ua",
    "sec-ch-ua-mobile": b"sec-ch-ua-mobile",
    "sec-ch-ua-platform": b"sec-ch-ua-platform",
    "sec-fetch-site": b"sec-fetch-site",
    "sec-fetch-mode": b"sec-fetch-mode",
    "sec-fetch-user": b"sec-fetch-user",
    "sec-fetch-dest": b"sec-fetch-dest",
    "x-forwarded-for": b"x-forwarded-for",
    "x-forwarded-proto": b"x-forwarded-proto",
    "x-forwarded-host": b"x-forwarded-host",
    "x-real-ip": b"x-real-ip",
}

cdef dict _HEADER_VAL_BYTES = {
    "*/*": b"*/*",
    "keep-alive": b"keep-alive",
    "close": b"close",
    "gzip, deflate": b"gzip, deflate",
    "gzip, deflate, br": b"gzip, deflate, br",
    "application/json": b"application/json",
    "text/plain": b"text/plain",
    "text/plain; charset=utf-8": b"text/plain; charset=utf-8",
    "text/html": b"text/html",
    "text/html; charset=utf-8": b"text/html; charset=utf-8",
}

# Caches and prebuilt lists for outbound RSGI
cdef list _PREBUILT_JSON_HEADERS = [("content-type", "application/json")]
cdef list _PREBUILT_TEXT_PLAIN_UTF8_HEADERS = [("content-type", "text/plain; charset=utf-8")]
cdef list _PREBUILT_TEXT_PLAIN_HEADERS = [("content-type", "text/plain")]
cdef list _PREBUILT_TEXT_HTML_UTF8_HEADERS = [("content-type", "text/html; charset=utf-8")]
cdef list _PREBUILT_TEXT_HTML_HEADERS = [("content-type", "text/html")]
cdef list _EMPTY_HEADERS = []

cdef dict _STATIC_HEADERS_BY_CT_BYTES = {
    b"application/json": _PREBUILT_JSON_HEADERS,
    b"text/plain; charset=utf-8": _PREBUILT_TEXT_PLAIN_UTF8_HEADERS,
    b"text/plain": _PREBUILT_TEXT_PLAIN_HEADERS,
    b"text/html; charset=utf-8": _PREBUILT_TEXT_HTML_UTF8_HEADERS,
    b"text/html": _PREBUILT_TEXT_HTML_HEADERS,
}

cdef dict _KNOWN_OUTBOUND_HEADER_NAME_STR = {
    b"content-type": "content-type",
    b"content-length": "content-length",
    b"server": "server",
    b"date": "date",
    b"set-cookie": "set-cookie",
    b"location": "location",
    b"connection": "connection",
    b"cache-control": "cache-control",
    b"vary": "vary",
    b"access-control-allow-origin": "access-control-allow-origin",
    b"access-control-allow-headers": "access-control-allow-headers",
    b"access-control-allow-methods": "access-control-allow-methods",
    b"access-control-allow-credentials": "access-control-allow-credentials",
    b"access-control-expose-headers": "access-control-expose-headers",
    b"access-control-max-age": "access-control-max-age",
    b"transfer-encoding": "transfer-encoding",
    b"www-authenticate": "www-authenticate",
    b"authorization": "authorization",
    b"accept": "accept",
    b"host": "host",
    b"etag": "etag",
    b"last-modified": "last-modified",
    b"strict-transport-security": "strict-transport-security",
    b"x-content-type-options": "x-content-type-options",
    b"x-frame-options": "x-frame-options",
}

cdef dict _KNOWN_OUTBOUND_HEADER_VAL_STR = {
    b"application/json": "application/json",
    b"text/plain; charset=utf-8": "text/plain; charset=utf-8",
    b"text/plain": "text/plain",
    b"text/html; charset=utf-8": "text/html; charset=utf-8",
    b"text/html": "text/html",
    b"chunked": "chunked",
    b"keep-alive": "keep-alive",
    b"close": "close",
    b"0": "0",
}

cdef dict _CT_STR_CACHE = {
    b"text/html; charset=utf-8": "text/html; charset=utf-8",
    b"text/html": "text/html",
    b"application/json": "application/json",
    b"text/plain": "text/plain",
    b"text/plain; charset=utf-8": "text/plain; charset=utf-8",
}

cdef extern from "interning.h":
    PyObject *get_interned_content_type_bytes(const char *type_str, size_t len)
    PyObject *get_interned_header_name_bytes(const char *name_str, size_t len)

cdef inline bytes intern_ct_bytes(bytes ct):
    if ct is None:
        return None
    cdef char *raw = PyBytes_AS_STRING(ct)
    cdef Py_ssize_t size = PyBytes_GET_SIZE(ct)
    cdef PyObject *interned = get_interned_content_type_bytes(raw, <size_t>size)
    if interned != NULL:
        return <bytes><object>interned
    return ct

MAX_RESPONSE_CHUNK_SIZE = 61440  # 64kb — Python-accessible
cdef int _MAX_RESPONSE_CHUNK_SIZE = MAX_RESPONSE_CHUNK_SIZE


cdef bint should_use_chunked_encoding(Content content):
    return content.length < 0


cpdef void set_headers_for_response_content(Response message):
    cdef Content content = message.content

    if not content:
        message._add_header(b'content-length', b'0')
        return

    message._add_header(b'content-type', intern_ct_bytes(content.type) if content.type else b'application/octet-stream')

    if should_use_chunked_encoding(content):
        message._add_header(b'transfer-encoding', b'chunked')
    else:
        message._add_header(b'content-length', str(content.length).encode())


cpdef bytes write_response_cookie(Cookie cookie):
    return write_cookie_for_response(cookie)


async def write_chunks(Content http_content):
    """
    Writes chunks for transfer encoding. This method only works when using
    `transfer-encoding: chunked`!
    """
    async for chunk in http_content.get_parts():
        yield (hex(len(chunk))).encode()[2:] + b'\r\n' + chunk + b'\r\n'
    yield b'0\r\n\r\n'


def get_chunks(bytes data):
    cdef Py_ssize_t i
    for i in range(0, len(data), _MAX_RESPONSE_CHUNK_SIZE):
        yield data[i:i + _MAX_RESPONSE_CHUNK_SIZE]
    yield b''


async def send_asgi_response(Response response, object send):
    cdef bytes chunk
    cdef Content content = response.content

    set_headers_for_response_content(response)

    await send({
        'type': 'http.response.start',
        'status': response.status,
        'headers': response._raw_headers
    })

    if content:
        if content.length < 0 or isinstance(content, StreamedContent):
            # NB: ASGI HTTP Servers automatically handle chunked encoding,
            # there is no need to write the length of each chunk
            # (see write_chunks function)
            closing_chunk = False
            async for chunk in content.get_parts():
                if not chunk:
                    closing_chunk = True
                await send({
                    'type': 'http.response.body',
                    'body': chunk,
                    'more_body': bool(chunk)
                })

            if not closing_chunk:
                # This is needed, otherwise uvicorn complains with:
                # ERROR:    ASGI callable returned without completing response.
                await send({
                    'type': 'http.response.body',
                    'body': b"",
                    'more_body': False
                })
        else:
            if content.length > _MAX_RESPONSE_CHUNK_SIZE:
                # Note: get_chunks yields the closing bytes fragment therefore
                # we do not need to check for the closing message!
                for chunk in get_chunks(content.body):
                    await send({
                        'type': 'http.response.body',
                        'body': chunk,
                        'more_body': bool(chunk)
                    })
            else:
                await send({
                    'type': 'http.response.body',
                    'body': content.body,
                    'more_body': False
                })
    else:
        await send({
            'type': 'http.response.body',
            'body': b''
        })


_NEW_LINES_RX = re.compile("\r\n|\n")


cpdef bytes write_sse(ServerSentEvent event):
    """
    Writes a ServerSentEvent object to bytes.
    """
    cdef bytearray value = bytearray()

    if event.id:
        value.extend(b"id: " + _NEW_LINES_RX.sub("", event.id).encode("utf8") + b"\n")

    if event.comment:
        for part in _NEW_LINES_RX.split(event.comment):
            value.extend(b": " + part.encode("utf8") + b"\n")

    if event.event:
        value.extend(b"event: " + _NEW_LINES_RX.sub("", event.event).encode("utf8") + b"\n")

    if event.data:
        value.extend(b"data: " + event.write_data().encode("utf8") + b"\n")

    if event.retry > -1:
        value.extend(b"retry: " + str(event.retry).encode() + b"\n")

    value.extend(b"\n")
    return bytes(value)


cpdef list extract_rsgi_headers(object raw_headers):
    cdef list headers = []
    cdef object items = getattr(raw_headers, "items", None)
    cdef object iter_source = items() if items is not None else raw_headers
    cdef object pair, name, value
    cdef str name_str, val_str

    if iter_source is None:
        return headers

    for pair in iter_source:
        name = pair[0]
        value = pair[1]

        if PyUnicode_CheckExact(name):
            name_str = <str>name
        elif PyBytes_CheckExact(name):
            name_str = (<bytes>name).decode("latin-1")
        else:
            name_str = str(name)

        if PyUnicode_CheckExact(value):
            val_str = <str>value
        elif PyBytes_CheckExact(value):
            val_str = (<bytes>value).decode("latin-1")
        else:
            val_str = str(value)

        headers.append((name_str, val_str))
    return headers


cpdef Request instantiate_rsgi_request(object scope, object protocol):
    cdef str path_str = scope.path
    cdef str query_str = scope.query_string or ""
    cdef str method = scope.method
    cdef Request request = acquire_request(method, path_str, query_str, None, scope)
    # Lazy RSGIContent: do not allocate RSGIContent on GET/HEAD/OPTIONS
    if method != "GET" and method != "HEAD" and method != "OPTIONS":
        request.content = RSGIContent(protocol)
    else:
        request.scope_protocol = protocol
    return request


cpdef object send_rsgi_response_sync(Response response, object protocol):
    cdef list raw_headers = response._raw_headers
    cdef Content content = response.content
    cdef list headers
    cdef str ct_str, name_str, val_str
    cdef bint has_ct
    cdef object h, name, val, body

    if not raw_headers:
        if content is not None and content.type is not None:
            headers = _STATIC_HEADERS_BY_CT_BYTES.get(content.type)
            if headers is None:
                ct_str = _CT_STR_CACHE.get(content.type)
                if ct_str is None:
                    ct_str = content.type.decode("latin-1") if PyBytes_CheckExact(content.type) else str(content.type)
                headers = [("content-type", ct_str)]
        else:
            headers = _EMPTY_HEADERS
    else:
        headers = []
        has_ct = False
        for h in raw_headers:
            name = h[0]
            val = h[1]
            if PyUnicode_CheckExact(name):
                name_str = <str>name
            elif PyBytes_CheckExact(name):
                name_str = _KNOWN_OUTBOUND_HEADER_NAME_STR.get(name)
                if name_str is None:
                    name_str = (<bytes>name).decode("latin-1")
            else:
                name_str = str(name)

            if PyUnicode_CheckExact(val):
                val_str = <str>val
            elif PyBytes_CheckExact(val):
                val_str = _KNOWN_OUTBOUND_HEADER_VAL_STR.get(val)
                if val_str is None:
                    val_str = (<bytes>val).decode("latin-1")
            else:
                val_str = str(val)

            if name == "content-type" or name == b"content-type" or name_str == "content-type":
                has_ct = True
            headers.append((name_str, val_str))

        if not has_ct and content is not None and content.type is not None:
            ct_str = _CT_STR_CACHE.get(content.type)
            if ct_str is None:
                ct_str = content.type.decode("latin-1") if PyBytes_CheckExact(content.type) else str(content.type)
            headers.append(("content-type", ct_str))

    if content is not None:
        file_path = getattr(content, "file_path", None)
        if file_path is not None and hasattr(protocol, "response_file"):
            file_range = getattr(content, "file_range", None)
            if file_range is not None and hasattr(protocol, "response_file_range"):
                protocol.response_file_range(response.status, headers, file_path, file_range[0], file_range[1])
                return None
            protocol.response_file(response.status, headers, file_path)
            return None

        body = content.body
        if body is not None:
            if PyBytes_CheckExact(body):
                protocol.response_bytes(response.status, headers, body)
                return None
            elif PyUnicode_CheckExact(body):
                protocol.response_str(response.status, headers, body)
                return None
            elif isinstance(body, (memoryview, bytearray)):
                protocol.response_bytes(response.status, headers, body)
                return None
            else:
                protocol.response_str(response.status, headers, str(body))
                return None

        if isinstance(content, StreamedContent):
            return _send_rsgi_stream(response, protocol, headers, content)

    protocol.response_empty(response.status, headers)
    return None


async def _send_rsgi_stream(Response response, object protocol, list headers, StreamedContent content):
    cdef object trx = await protocol.response_stream(response.status, headers)
    cdef object chunk
    async for chunk in content.stream():
        if chunk:
            if PyBytes_CheckExact(chunk):
                await trx.send_bytes(chunk)
            elif PyUnicode_CheckExact(chunk):
                await trx.send_str(chunk)
            elif isinstance(chunk, (memoryview, bytearray)):
                await trx.send_bytes(chunk)
            else:
                await trx.send_str(str(chunk))


async def send_rsgi_response(Response response, object protocol):
    cdef object res = send_rsgi_response_sync(response, protocol)
    if res is not None:
        await res


async def _dispatch_rsgi_async(object app, Request request, object res, object protocol):
    cdef Response response
    try:
        response = await res
        res_sync = send_rsgi_response_sync(response, protocol)
        if res_sync is not None:
            await res_sync
        if isinstance(response, Response):
            release_response(response)
    finally:
        request.scope = None
        release_request(request)


async def _await_res_sync(object res_sync, Response response, Request request):
    try:
        await res_sync
        if isinstance(response, Response):
            release_response(response)
    finally:
        request.scope = None
        release_request(request)


cpdef object dispatch_rsgi_http(object app, object scope, object protocol):
    cdef Request request = instantiate_rsgi_request(scope, protocol)
    cdef object res
    cdef Response response
    cdef object res_sync

    res = app.handle(request)
    if not isinstance(res, Response):
        return _dispatch_rsgi_async(app, request, res, protocol)

    response = <Response>res
    res_sync = send_rsgi_response_sync(response, protocol)
    if res_sync is not None:
        return _await_res_sync(res_sync, response, request)

    release_response(response)
    request.scope = None
    release_request(request)
    return None
