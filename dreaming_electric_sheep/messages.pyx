# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
# cython: language_level=3
# Copyright (C) 2018-present Roberto Prevato
#
# This module is part of Dreaming Electric Sheep and is released under
# the MIT License https://opensource.org/licenses/MIT

import asyncio
import http
import re
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from urllib.parse import parse_qs, quote, unquote, urlencode

import msgspec
from guardpost import Identity

from dreaming_electric_sheep.sessions import Session
from dreaming_electric_sheep.settings.encodings import encodings_settings
from dreaming_electric_sheep.settings.json import json_settings
from dreaming_electric_sheep.utils.time import utcnow

from .contents cimport (
    ASGIContent,
    Content,
    RSGIContent,
    parse_www_form_urlencoded,
)
from .cookies cimport Cookie, parse_cookie, split_value, write_cookie_for_response
from .exceptions cimport (
    BadRequest,
    BadRequestFormat,
    FailedRequestError,
    MessageAborted,
)
from .headers cimport Headers
from .url cimport URL, build_absolute_url

from cpython.object cimport PyObject
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_GET_SIZE, PyBytes_CheckExact
from cpython.unicode cimport PyUnicode_AsUTF8AndSize, PyUnicode_CheckExact
from libc.string cimport memcmp

cdef extern from "interning.h":
    PyObject *get_interned_method_str(const char *method_str, size_t len)
    PyObject *get_interned_method_bytes(const char *method_str, size_t len)
    PyObject *get_interned_header_name_bytes(const char *name_str, size_t len)
    PyObject *get_interned_content_type_bytes(const char *type_str, size_t len)

cdef inline str intern_method_str(str method):
    if method is None:
        return None
    cdef Py_ssize_t size = 0
    cdef const char *raw = PyUnicode_AsUTF8AndSize(method, &size)
    if raw == NULL or size == 0:
        return method
    cdef PyObject *interned = get_interned_method_str(raw, <size_t>size)
    if interned != NULL:
        return <str><object>interned
    return method

cdef inline bytes intern_header_name_bytes(bytes name):
    if name is None:
        return None
    cdef char *raw = PyBytes_AS_STRING(name)
    cdef Py_ssize_t size = PyBytes_GET_SIZE(name)
    cdef PyObject *interned = get_interned_header_name_bytes(raw, <size_t>size)
    if interned != NULL:
        return <bytes><object>interned
    return name

_charset_rx = re.compile(rb"charset=([\w\-]+)", re.I)


cpdef str parse_charset(bytes value):
    m = _charset_rx.search(value)
    if m:
        return m.group(1).decode("ascii")
    return None


async def _read_stream(request):
    async for _ in request.content.stream():  # type: ignore
        pass


async def _call_soon(coro):
    """
    Returns the output of a coroutine if its result is immediately available,
    otherwise None.
    """
    task = asyncio.create_task(coro)
    asyncio.get_event_loop().call_soon(task.cancel)
    try:
        return await task
    except asyncio.CancelledError:
        return None


def _encode(value):
    return value.encode("utf8") if value else None


async def _multipart_to_dict_streaming(
    stream_iter,
    spool_max_size=1024 * 1024,
):
    """
    Convert streaming multipart parts to dictionary with memory-efficient file handling.

    Files are wrapped in FileBuffer with SpooledTemporaryFile:
    - Small files (<1MB): Kept in memory for performance
    - Large files (>1MB): Automatically spooled to temporary disk files
    - Form fields: Buffered in memory with size limits

    Args:
        stream_iter: Async iterator of StreamedFormPart objects
        spool_max_size: Threshold for spooling files to disk (default: 1MB)

    Returns:
        Dictionary with form data and FileBuffer instances for files
    """
    from collections import defaultdict
    from tempfile import SpooledTemporaryFile

    from .contents import FormPart

    data = defaultdict(list)

    async for part in stream_iter:
        key = part.name

        spooled_file = SpooledTemporaryFile(max_size=spool_max_size, mode="w+b")
        total_size = 0

        async for chunk in part.stream():
            spooled_file.write(chunk)
            total_size += len(chunk)
        spooled_file.seek(0)

        # TODO: encoding below is for backward compatibility
        # TODO: remove in v3
        item = FormPart(
            name=_encode(part.name),
            data=spooled_file,
            file_name=_encode(part.file_name),
            content_type=_encode(part.content_type),
            size=total_size,
            charset=_encode(part.charset),
        )
        data[key].append(item)

    return dict(data)


cdef inline bint _msg_header_key_matches(object h_name, bytes low_bkey, str low_skey):
    if PyBytes_CheckExact(h_name):
        return (<bytes>h_name).lower() == low_bkey
    elif PyUnicode_CheckExact(h_name):
        return (<str>h_name).lower() == low_skey
    else:
        return str(h_name).lower() == low_skey

cdef inline object _msg_convert_val(object val, bint is_bytes):
    if val is None:
        return None
    if is_bytes:
        if PyBytes_CheckExact(val):
            return val
        elif PyUnicode_CheckExact(val):
            return (<str>val).encode("latin-1")
        return str(val).encode("latin-1")
    else:
        if PyUnicode_CheckExact(val):
            return val
        elif PyBytes_CheckExact(val):
            return (<bytes>val).decode("latin-1")
        return str(val)

cdef list _extract_headers_from_scope(object raw_headers):
    cdef list headers = []
    if raw_headers is None:
        return headers
    cdef object items = getattr(raw_headers, "items", None)
    cdef object iter_source = items() if items is not None else raw_headers
    cdef object pair, name, value
    cdef bytes name_bytes
    if iter_source is None:
        return headers
    for pair in iter_source:
        name = pair[0]
        value = pair[1]
        if PyBytes_CheckExact(name):
            name_bytes = intern_header_name_bytes(<bytes>name)
        elif PyUnicode_CheckExact(name):
            name_bytes = intern_header_name_bytes((<str>name).encode("latin-1"))
        else:
            name_bytes = intern_header_name_bytes(str(name).encode("latin-1"))
        headers.append((name_bytes, value))
    return headers


cdef class Message:

    def __init__(self, list headers):
        self._raw_headers = [(intern_header_name_bytes(h[0]), h[1]) if isinstance(h, tuple) and len(h) == 2 and isinstance(h[0], bytes) else h for h in headers] if headers is not None else []

    cdef void _ensure_raw_headers(self):
        if self._raw_headers is None:
            if hasattr(self, "scope") and getattr(self, "scope") is not None and hasattr(getattr(self, "scope"), "headers"):
                self._raw_headers = _extract_headers_from_scope(getattr(self, "scope").headers)
            else:
                self._raw_headers = []

    @property
    def headers(self):
        if self._headers is not None:
            return self._headers
        if self._raw_headers is None:
            self._ensure_raw_headers()
        self._headers = Headers(self._raw_headers)
        return self._headers

    cpdef Message with_content(self, Content content):
        self.content = content
        return self

    cpdef object get_first_header(self, object key):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        cdef tuple header
        cdef bytes low_bkey
        cdef str low_skey
        cdef bint is_bytes = PyBytes_CheckExact(key)

        if is_bytes:
            low_bkey = intern_header_name_bytes((<bytes>key).lower())
            low_skey = low_bkey.decode("latin-1")
        elif PyUnicode_CheckExact(key):
            low_skey = (<str>key).lower()
            low_bkey = low_skey.encode("latin-1")
        else:
            low_skey = str(key).lower()
            low_bkey = low_skey.encode("latin-1")

        for header in self._raw_headers:
            if _msg_header_key_matches(header[0], low_bkey, low_skey):
                return _msg_convert_val(header[1], is_bytes)
        return None

    cpdef list get_headers(self, object key):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        cdef list results = []
        cdef tuple header
        cdef bytes low_bkey
        cdef str low_skey
        cdef bint is_bytes = PyBytes_CheckExact(key)

        if is_bytes:
            low_bkey = intern_header_name_bytes((<bytes>key).lower())
            low_skey = low_bkey.decode("latin-1")
        elif PyUnicode_CheckExact(key):
            low_skey = (<str>key).lower()
            low_bkey = low_skey.encode("latin-1")
        else:
            low_skey = str(key).lower()
            low_bkey = low_skey.encode("latin-1")

        for header in self._raw_headers:
            if _msg_header_key_matches(header[0], low_bkey, low_skey):
                results.append(_msg_convert_val(header[1], is_bytes))
        return results

    cdef void init_prop(self, str name, object value):
        """
        This method is for internal use and only accessible in Cython.
        It initializes a new property on the request object, for rare scenarios
        where an additional property can be useful. It would also be possible
        to use a weakref.WeakKeyDictionary to store additional information
        about request objects when useful, but for simplicity this method uses
        the object __dict__.
        """
        try:
            getattr(self, name)
        except AttributeError:
            setattr(self, name, value)

    cdef list get_headers_tuples(self, object key):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        cdef list results = []
        cdef tuple header
        cdef bytes low_bkey
        cdef str low_skey

        if PyBytes_CheckExact(key):
            low_bkey = intern_header_name_bytes((<bytes>key).lower())
            low_skey = low_bkey.decode("latin-1")
        elif PyUnicode_CheckExact(key):
            low_skey = (<str>key).lower()
            low_bkey = low_skey.encode("latin-1")
        else:
            low_skey = str(key).lower()
            low_bkey = low_skey.encode("latin-1")

        for header in self._raw_headers:
            if _msg_header_key_matches(header[0], low_bkey, low_skey):
                results.append(header)
        return results

    cpdef object get_single_header(self, object key):
        cdef list results = self.get_headers(key)
        if len(results) > 1:
            raise ValueError('Headers contains more than one header with the given key')
        if len(results) < 1:
            raise ValueError('Headers does not contain one header with the given key')
        return results[0]

    cpdef void remove_header(self, object key):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        cdef tuple header
        cdef list to_remove = []
        cdef bytes low_bkey
        cdef str low_skey

        if PyBytes_CheckExact(key):
            low_bkey = intern_header_name_bytes((<bytes>key).lower())
            low_skey = low_bkey.decode("latin-1")
        elif PyUnicode_CheckExact(key):
            low_skey = (<str>key).lower()
            low_bkey = low_skey.encode("latin-1")
        else:
            low_skey = str(key).lower()
            low_bkey = low_skey.encode("latin-1")

        for header in self._raw_headers:
            if _msg_header_key_matches(header[0], low_bkey, low_skey):
                to_remove.append(header)

        for header in to_remove:
            self._raw_headers.remove(header)

    cdef void remove_headers(self, list headers):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        cdef tuple header
        for header in headers:
            self._raw_headers.remove(header)

    cdef bint _has_header(self, object key):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        cdef bytes low_bkey
        cdef str low_skey

        if PyBytes_CheckExact(key):
            low_bkey = intern_header_name_bytes((<bytes>key).lower())
            low_skey = low_bkey.decode("latin-1")
        elif PyUnicode_CheckExact(key):
            low_skey = (<str>key).lower()
            low_bkey = low_skey.encode("latin-1")
        else:
            low_skey = str(key).lower()
            low_bkey = low_skey.encode("latin-1")

        for existing_key, existing_value in self._raw_headers:
            if _msg_header_key_matches(existing_key, low_bkey, low_skey):
                return True
        return False

    cpdef bint has_header(self, object key):
        return self._has_header(key)

    cdef void _add_header(self, object key, object value):
        if self._raw_headers is None:
            self._ensure_raw_headers()
        if PyBytes_CheckExact(key):
            self._raw_headers.append((intern_header_name_bytes(<bytes>key), value))
        else:
            self._raw_headers.append((key, value))

    cdef void _add_header_if_missing(self, object key, object value):
        if not self._has_header(key):
            self._add_header(key, value)

    cpdef void add_header(self, object key, object value):
        self._add_header(key, value)

    cpdef void set_header(self, object key, object value):
        self.remove_header(key)
        self._add_header(key, value)

    cpdef object content_type(self):
        if self.content and self.content.type:
            return self.content.type
        return self.get_first_header(b'content-type')

    async def read(self):
        if self.content:
            return await self.content.read()
        if self.scope_protocol is not None:
            self.content = RSGIContent(self.scope_protocol)
            return await self.content.read()
        return None

    async def read_raw(self):
        """
        Reads and returns the raw binary body without string conversion,
        implementing Python's buffer protocol (Py_buffer compatible: bytes/bytearray).
        """
        if self.content:
            return await self.content.read()
        if self.scope_protocol is not None:
            self.content = RSGIContent(self.scope_protocol)
            return await self.content.read()
        return b''

    async def read_buffer(self):
        """
        Reads request body returning a memoryview suitable for zero-copy
        interoperability with PyTorch tensors (torch.frombuffer), DLPack, and NumPy.
        """
        if self.content:
            if hasattr(self.content, "read_buffer"):
                return await self.content.read_buffer()
            raw = await self.content.read()
            if raw is None:
                return memoryview(b"")
            return memoryview(raw) if isinstance(raw, (bytes, bytearray, memoryview)) else memoryview(bytes(raw))
        if self.scope_protocol is not None:
            self.content = RSGIContent(self.scope_protocol)
            return await self.content.read_buffer()
        return memoryview(b"")

    async def read_detached(self):
        """
        Reads and returns an independent copy (bytes) of the body buffer,
        guaranteeing safe usage across background tasks (e.g. asyncio.create_task)
        without risk of use-after-free or socket buffer recycling.
        """
        raw = await self.read_raw()
        if raw is None:
            return b""
        return bytes(raw)

    def detach_raw(self):
        """
        Synchronously returns an independent copy (bytes) of already-read body buffer,
        guaranteeing safe usage across background tasks without holding socket buffer pointers.
        """
        if self.content:
            data = getattr(self.content, "_data", None)
            if data is not None:
                return bytes(data)
            body = getattr(self.content, "body", None)
            if body is not None:
                return bytes(body)
        return b""

    @property
    def body_buffer(self):
        """
        Returns a memoryview over the body buffer, supporting zero-copy operations.
        """
        if self.content:
            return getattr(self.content, "body_buffer", memoryview(b""))
        return memoryview(b"")

    async def stream(self):
        if self.content is None and self.scope_protocol is not None:
            self.content = RSGIContent(self.scope_protocol)
        if self.content:
            async for chunk in self.content.stream():
                yield chunk
        else:
            yield None

    async def text(self):
        body = await self.read()
        if body is None:
            return ""
        try:
            return body.decode(self.charset)
        except UnicodeDecodeError as decode_error:
            return encodings_settings.decode(body, decode_error)

    async def form(self, simplify_fields=True):
        """
        Parse form data from the request with memory-efficient file handling, but
        reading text inputs whole in memory. To handle big text input fields, use
        `multipart()` which doesn't read automatically text fields in memory or
        `multipart_stream()` for streaming without any buffering.

        This method now uses SpooledTemporaryFile for multipart uploads:
        - Small files (<1MB): Kept in memory for performance
        - Large files (>1MB): Automatically spooled to temporary disk files
        - No memory exhaustion on large uploads!

        File uploads are returned as `FileBuffer` instances (not bytes!).
        Form fields are returned as strings.

        Returns:
            Dictionary with form data. File uploads are FileBuffer instances.

        Example:
            ```python
            form_data = await request.form()

            # Form fields are strings
            name = form_data.get("name")  # str

            # Files are FileBuffer instances
            avatar = form_data.get("avatar")  # FileBuffer
            if isinstance(avatar, FileBuffer):
                # Save without loading into memory
                with open(f"uploads/{avatar.filename}", "wb") as f:
                    avatar.seek(0)
                    f.write(avatar.read())
                avatar.close()
            ```
        """
        cdef str text
        cdef bytes content_type_value = self.content_type()

        if not content_type_value:
            return None

        if self._form_data is not None:
            if b'multipart/form-data;' in content_type_value and simplify_fields:
                # This is just to not break backward compatibility.
                # TODO: consider removing this in v3
                from .contents import simplify_multipart_data
                return simplify_multipart_data(self._form_data)
            return self._form_data

        if b'application/x-www-form-urlencoded' in content_type_value:
            text = await self.text()
            return parse_www_form_urlencoded(text)
        if b'multipart/form-data;' in content_type_value:
            # In this case, multipart/form-data is handled in a memory efficient way,
            # which does not support reading the request stream more than once and
            # requires disposal at the end of the request-response cycle.
            # Request form is intentionally not kept in memory if multipart_stream
            # is read directly by the user.
            from .contents import simplify_multipart_data
            self._form_data = await _multipart_to_dict_streaming(
                self.multipart_stream()
            )
            return (
                simplify_multipart_data(self._form_data)
                if simplify_fields
                else self._form_data
            )
        return None

    async def multipart(self):
        """
        Parse multipart/form-data with memory-efficient part handling, relying on
        SpooledTemporaryFile. **Note:** for true streaming without any buffering,
        use `multipart_stream()`.

        This method uses SpooledTemporaryFile for field and file uploads:
        - Small data (<1MB): Kept in memory
        - Large data (>1MB): Automatically spooled to temporary disk files

        Returns:
            List of FormPart, or None
        """
        items = []
        data = await self.form(simplify_fields=False)
        if not data:
            return items
        for _, values in data.items():
            for value in values:
                items.append(value)
        return items

    async def multipart_stream(self):
        """
        Parse multipart/form-data lazily from the request stream.

        This method streams and parses multipart data without loading the entire
        request body into memory, making it suitable for large file uploads and large
        text uploads.

        Yields:
            FormPart objects as they are parsed from the stream.

        Example:
            ```python
            async def upload_handler(request):
                async for part in request.multipart_stream():
                    if part.file_name:
                        # Process file part
                        await save_file(part.file_name, part.data)
                    else:
                        # Process form field
                        value = part.data.decode('utf-8')
            ```
        """
        cdef bytes content_type_value = self.content_type()
        if not content_type_value:
            return

        if b'multipart/form-data;' not in content_type_value:
            return

        # Extract boundary from Content-Type header
        # e.g., "multipart/form-data; boundary=----WebKitFormBoundary..."
        from dreaming_electric_sheep.multipart import get_boundary_from_header, parse_multipart_async
        try:
            boundary = get_boundary_from_header(content_type_value)
        except (ValueError, IndexError):
            return

        async for part in parse_multipart_async(self.stream(), boundary):
            yield part

    cpdef bint declares_content_type(self, object type):
        cdef object content_type = self.content_type()
        if not content_type:
            return False

        cdef str ct_str = content_type.decode("latin-1") if PyBytes_CheckExact(content_type) else str(content_type)
        cdef str t_str = type.decode("latin-1") if PyBytes_CheckExact(type) else str(type)

        # NB: we look for substring intentionally here
        if t_str.lower() in ct_str.lower():
            return True
        return False

    cpdef bint declares_json(self):
        return self.declares_content_type(b'json')

    cpdef bint declares_xml(self):
        return self.declares_content_type(b'xml')

    async def files(self, name=None):
        if isinstance(name, str):
            # Note: FormPart fields are not decoded (TODO: decode them in v3).
            name = name.encode('utf8')
        data = await self.multipart()
        if data is None:
            return []
        if name:
            return [part for part in data if part.file_name and part.name == name]
        return [part for part in data if part.file_name]

    async def json(self, loads=None):
        if not self.declares_json():
            return None

        raw = await self.read_raw()
        if raw is None or len(raw) == 0:
            return None

        if loads is None and json_settings.has_custom_loads:
            loads = json_settings.loads

        if loads is None:
            try:
                return msgspec.json.decode(raw)
            except msgspec.DecodeError as decode_error:
                content_type = self.content_type()
                if content_type and b'json' in content_type:
                    raise BadRequestFormat(
                        f'Declared Content-Type is {content_type.decode()} but '
                        f'the content cannot be parsed as JSON.', decode_error
                    )
                raise BadRequestFormat(
                    f'Cannot parse content as JSON',
                    decode_error
                )
        else:
            try:
                text = raw.decode(self.charset) if isinstance(raw, (bytes, bytearray, memoryview)) else raw
                return loads(text)
            except (JSONDecodeError, UnicodeDecodeError, ValueError) as decode_error:
                content_type = self.content_type()
                if content_type and b'json' in content_type:
                    raise BadRequestFormat(
                        f'Declared Content-Type is {content_type.decode()} but '
                        f'the content cannot be parsed as JSON.', decode_error
                    )
                raise BadRequestFormat(
                    f'Cannot parse content as JSON',
                    decode_error
                )

    cpdef bint has_body(self):
        cdef Content content = self.content
        if not content or content.length == 0:
            return False
        # NB: if we use chunked encoding, we don't know the content.length;
        # and it is set to -1 (in contents.pyx), therefore it is handled
        # properly
        return True

    @property
    def charset(self):
        content_type = self.content_type()
        if content_type:
            return parse_charset(content_type) or 'utf8'
        return 'utf8'


cpdef bint method_without_body(str method):
    return method == 'GET' or method == 'HEAD' or method == 'TRACE'


cdef class Request(Message):

    def __cinit__(self, *args, **kwargs):
        self._arena_initialized = False

    def __dealloc__(self):
        if self._arena_initialized:
            scratchpad_destroy(&self._arena)
            self._arena_initialized = False

    def __init__(
        self,
        str method,
        bytes url,
        list headers
    ):
        cdef URL _url = URL(url) if url else None
        self._raw_headers = [(intern_header_name_bytes(h[0]), h[1]) if isinstance(h, tuple) and len(h) == 2 and isinstance(h[0], bytes) else h for h in headers] if headers else []
        self.method = intern_method_str(method)
        self._url = _url
        self._session = None
        if _url:
            self._path = _url.path
            self._raw_query = _url.query

    cdef void *alloc_scratchpad(self, size_t size, size_t alignment=64):
        if not self._arena_initialized:
            scratchpad_init(&self._arena, 65536)
            self._arena_initialized = True
        cdef void *ptr = NULL
        cdef des_err err = scratchpad_alloc(&self._arena, size, alignment, &ptr)
        if err != DES_OK:
            return NULL
        return ptr

    def scratchpad_arena_stats(self):
        """Returns (capacity, offset, is_initialized) for arena debugging/monitoring."""
        if not self._arena_initialized:
            return (0, 0, False)
        return (self._arena.capacity, self._arena.offset, True)

    # TODO: deprecate the 'identity' property in the future. This requires a
    # breaking change in guardpost, too.
    @property
    def identity(self):
        return self.user

    @identity.setter
    def identity(self, value):
        self._user = value

    @property
    def user(self):
        if self._user is None:
            self._user = Identity()  # no claims, unauthenticated
        return self._user

    @user.setter
    def user(self, value):
        self._user = value

    @property
    def scheme(self) -> str:
        if self._scheme is not None:
            return self._scheme
        if self.scope:
            return self.scope.get("scheme", "")
        return ""

    @scheme.setter
    def scheme(self, value: str):
        self._scheme = value

    @property
    def host(self) -> str:
        if self._host is not None:
            return self._host
        if self._url is not None and self._url.is_absolute:
            self._host = self._url.host.decode() if self._url.host is not None else ""
            return self._host
        host_header = self.get_first_header(b'host')
        if host_header is not None:
            self._host = host_header.decode()
            return self._host
        raise BadRequest("Missing Host header")

    @host.setter
    def host(self, value: str) -> None:
        self._host = value

    @property
    def base_path(self) -> str:
        if self._base_path is not None:
            return self._base_path
        if self.scope is not None:
            try:
                return self.scope.get("root_path", "")
            except AttributeError:
                pass
        return ""

    @base_path.setter
    def base_path(self, value: str):
        self._base_path = value

    @property
    def client_ip(self) -> str:
        if self.scope is None:
            return ""
        try:
            client_ip, client_port = self.scope.get("client", ("", 0))
            return client_ip
        except Exception:
            return ""

    @property
    def original_client_ip(self) -> str:
        if self._original_client_ip is not None:
            return self._original_client_ip
        return self.client_ip

    @original_client_ip.setter
    def original_client_ip(self, value: str):
        self._original_client_ip = value

    @property
    def session(self):
        if self._session is None:
            raise TypeError(
                "A session is not configured for this request, activate "
                "sessions using `app.use_sessions` method."
            )
        return self._session

    @session.setter
    def session(self, value: Session):
        self._session = value

    cpdef void reset(self):
        self.method = ""
        self._url = None
        self._path = ""
        self._raw_query = ""
        self.route_values = None
        self.scope = None
        self.scope_protocol = None
        self.identity = None
        self._user = None
        self._di_scope = None
        self.state = None
        self._session = None
        self._base_path = None
        self._original_client_ip = None
        self._host = None
        self._scheme = None
        self.context = None
        self.services = None
        self._form_data = None
        self._headers = None
        self._raw_headers = []
        self._is_disconnected = None
        if self.content is not None:
            self.content.dispose()
            self.content = None
        if self._arena_initialized:
            scratchpad_reset(&self._arena)

    @property
    def path(self) -> str:
        if isinstance(self._path, str):
            return self._path
        elif isinstance(self._path, bytes):
            return (<bytes>self._path).decode("utf8")
        return ""

    @property
    def raw_path(self) -> bytes:
        if isinstance(self._path, bytes):
            return <bytes>self._path
        elif isinstance(self._path, str):
            return (<str>self._path).encode("utf8")
        return b""

    @property
    def raw_query(self):
        return self._raw_query

    @classmethod
    def incoming(cls, object method, object path, object query, list headers, object scope=None):
        cdef str m_str = method if isinstance(method, str) else (<bytes>method).decode("latin-1")
        return acquire_request(m_str, path, query, headers, scope)

    @property
    def query(self):
        if self._raw_query:
            if isinstance(self._raw_query, str):
                return parse_qs(<str>self._raw_query)
            elif isinstance(self._raw_query, bytes):
                return parse_qs((<bytes>self._raw_query).decode("latin-1"))
        return {}

    @query.setter
    def query(self, value):
        cdef bytes raw_query
        raw_query = urlencode(value, True).encode("utf8")
        self._raw_query = raw_query
        self.url = self.url.with_query(raw_query)

    cpdef object get_query_param(self, object name, object default=None):
        if not self._raw_query or name is None:
            return default

        cdef bytes raw_bytes
        if PyBytes_CheckExact(self._raw_query):
            raw_bytes = <bytes>self._raw_query
        elif PyUnicode_CheckExact(self._raw_query):
            raw_bytes = (<str>self._raw_query).encode("latin-1")
        else:
            return default

        cdef bytes key_bytes
        if PyBytes_CheckExact(name):
            key_bytes = <bytes>name
        elif PyUnicode_CheckExact(name):
            key_bytes = (<str>name).encode("utf8")
        else:
            key_bytes = str(name).encode("utf8")

        cdef const char *q = PyBytes_AS_STRING(raw_bytes)
        cdef Py_ssize_t q_len = PyBytes_GET_SIZE(raw_bytes)
        cdef const char *k = PyBytes_AS_STRING(key_bytes)
        cdef Py_ssize_t k_len = PyBytes_GET_SIZE(key_bytes)

        if q_len == 0 or k_len == 0:
            return default

        cdef Py_ssize_t i = 0
        cdef Py_ssize_t val_start
        cdef Py_ssize_t val_end
        cdef bytes val_bytes
        cdef str val_str
        cdef bint has_pct_or_plus

        while i < q_len:
            if (i == 0 or q[i - 1] == c'&' or q[i - 1] == c';') and (i + k_len <= q_len) and (memcmp(q + i, k, k_len) == 0):
                if i + k_len == q_len or q[i + k_len] == c'&' or q[i + k_len] == c';':
                    return ""
                elif q[i + k_len] == c'=':
                    val_start = i + k_len + 1
                    val_end = val_start
                    has_pct_or_plus = False
                    while val_end < q_len and q[val_end] != c'&' and q[val_end] != c';':
                        if q[val_end] == c'%' or q[val_end] == c'+':
                            has_pct_or_plus = True
                        val_end += 1
                    val_bytes = raw_bytes[val_start:val_end]
                    if has_pct_or_plus:
                        val_str = unquote(val_bytes.replace(b'+', b' ').decode("utf8", "replace"))
                    else:
                        val_str = val_bytes.decode("utf8", "replace")
                    return val_str
            while i < q_len and q[i] != c'&' and q[i] != c';':
                i += 1
            i += 1

        return default

    cpdef list get_query_params(self, object name):
        cdef list results = []
        if not self._raw_query or name is None:
            return results

        cdef bytes raw_bytes
        if PyBytes_CheckExact(self._raw_query):
            raw_bytes = <bytes>self._raw_query
        elif PyUnicode_CheckExact(self._raw_query):
            raw_bytes = (<str>self._raw_query).encode("latin-1")
        else:
            return results

        cdef bytes key_bytes
        if PyBytes_CheckExact(name):
            key_bytes = <bytes>name
        elif PyUnicode_CheckExact(name):
            key_bytes = (<str>name).encode("utf8")
        else:
            key_bytes = str(name).encode("utf8")

        cdef const char *q = PyBytes_AS_STRING(raw_bytes)
        cdef Py_ssize_t q_len = PyBytes_GET_SIZE(raw_bytes)
        cdef const char *k = PyBytes_AS_STRING(key_bytes)
        cdef Py_ssize_t k_len = PyBytes_GET_SIZE(key_bytes)

        if q_len == 0 or k_len == 0:
            return results

        cdef Py_ssize_t i = 0
        cdef Py_ssize_t val_start
        cdef Py_ssize_t val_end
        cdef bytes val_bytes
        cdef str val_str
        cdef bint has_pct_or_plus

        while i < q_len:
            if (i == 0 or q[i - 1] == c'&' or q[i - 1] == c';') and (i + k_len <= q_len) and (memcmp(q + i, k, k_len) == 0):
                if i + k_len == q_len or q[i + k_len] == c'&' or q[i + k_len] == c';':
                    results.append("")
                elif q[i + k_len] == c'=':
                    val_start = i + k_len + 1
                    val_end = val_start
                    has_pct_or_plus = False
                    while val_end < q_len and q[val_end] != c'&' and q[val_end] != c';':
                        if q[val_end] == c'%' or q[val_end] == c'+':
                            has_pct_or_plus = True
                        val_end += 1
                    val_bytes = raw_bytes[val_start:val_end]
                    if has_pct_or_plus:
                        val_str = unquote(val_bytes.replace(b'+', b' ').decode("utf8", "replace"))
                    else:
                        val_str = val_bytes.decode("utf8", "replace")
                    results.append(val_str)
            while i < q_len and q[i] != c'&' and q[i] != c';':
                i += 1
            i += 1

        return results

    @property
    def is_htmx(self) -> bool:
        return self._has_header(b"hx-request")

    @property
    def htmx_target(self):
        cdef object val = self.get_first_header(b"hx-target")
        if val is None:
            return None
        return val.decode("utf8") if isinstance(val, bytes) else str(val)

    @property
    def htmx_trigger(self):
        cdef object val = self.get_first_header(b"hx-trigger")
        if val is None:
            return None
        return val.decode("utf8") if isinstance(val, bytes) else str(val)

    @property
    def htmx_current_url(self):
        cdef object val = self.get_first_header(b"hx-current-url")
        if val is None:
            return None
        return val.decode("utf8") if isinstance(val, bytes) else str(val)

    @property
    def htmx_prompt(self):
        cdef object val = self.get_first_header(b"hx-prompt")
        if val is None:
            return None
        return val.decode("utf8") if isinstance(val, bytes) else str(val)

    @property
    def htmx_target_id(self):
        cdef object target = self.htmx_target
        if target is None:
            return None
        if target.startswith("#"):
            return target[1:]
        return target

    @property
    def url(self):
        if self._url:
            return self._url

        cdef bytes b_path = self.raw_path
        cdef bytes b_query
        if isinstance(self._raw_query, bytes):
            b_query = <bytes>self._raw_query
        elif isinstance(self._raw_query, str):
            b_query = (<str>self._raw_query).encode("latin-1")
        else:
            b_query = b""

        if b_query:
            self._url = URL(b_path + b'?' + b_query)
        else:
            self._url = URL(b_path)
        return self._url

    @url.setter
    def url(self, object value):
        cdef URL _url

        if value:
            if isinstance(value, bytes):
                _url = URL(value)
            elif isinstance(value, str):
                _url = URL(value.encode('utf8'))
            elif isinstance(value, URL):
                _url = value
            else:
                raise TypeError('Invalid value type, expected bytes, str, or URL')
        else:
            _url = None

        if _url:
            self._path = _url.path
            self._raw_query = _url.query
        else:
            self._path = None
            self._raw_query = None
        self._url = _url
        # unset the cached host
        self._host = None
        self.remove_header(b"host")

    def __repr__(self):
        return f'<Request {self.method} {self.url.value.decode()}>'

    @property
    def cookies(self):
        cdef bytes header
        cdef list cookies_headers
        cdef dict cookies = {}

        cookies_headers = self.get_headers(b'cookie')
        if cookies_headers:
            for header in cookies_headers:
                # a single cookie header is expected from the client, but anyway here
                # multiple headers are handled:
                pairs = header.split(b'; ')

                for fragment in pairs:
                    try:
                        name, value = split_value(fragment, b"=")
                    except ValueError as unpack_error:
                        # discard cookie: in this case it's better to eat the exception
                        # than blocking a request just because a cookie is malformed
                        pass
                    else:
                        cookies[unquote(name.decode())] = unquote(value.rstrip(b'; ').decode())
        return cookies

    def get_cookie(self, str name):
        return self.cookies.get(name)

    def set_cookie(self, str name, str value):
        """
        Sets a cookie in the request. This method also ensures that a single
        `cookie` header is set on the request.
        """
        cdef bytes new_value
        cdef bytes existing_cookie

        new_value = (quote(name) + "=" + quote(value)).encode()
        existing_cookie = self.get_first_header(b"cookie")

        if existing_cookie:
            self.set_header(b"cookie", existing_cookie + b";" + new_value)
        else:
            self._raw_headers.append((b"cookie", new_value))

    @property
    def etag(self):
        return self.get_first_header(b"etag")

    @property
    def if_none_match(self):
        return self.get_first_header(b"if-none-match")

    cpdef bint expect_100_continue(self):
        cdef bytes value
        value = self.get_first_header(b'expect')
        if value and value.lower() == b'100-continue':
            return True
        return False

    async def is_disconnected(self):
        if not isinstance(self.content, ASGIContent):
            raise TypeError(
                "This method is only supported when a request is bound to "
                "an instance of ASGIContent and to an ASGI "
                "request/response cycle."
            )

        if self._is_disconnected is None:
            self._is_disconnected = False
        if self._is_disconnected is True:
            return True

        try:
            await _call_soon(_read_stream(self))
        except MessageAborted:
            self._is_disconnected = True

        return self._is_disconnected

    def dispose(self):
        if self._form_data is not None:
            for parts in self._form_data.values():
                for part in parts:
                    if part.file:
                        part.file.close()
        if self.content:
            self.content.dispose()  # type: ignore


cdef class Response(Message):

    def __init__(
        self,
        int status,
        list headers = None,
        Content content = None
    ):
        self._raw_headers = headers or []
        self.status = status
        self.content = content

    def __repr__(self):
        return f'<Response {self.status}>'

    @property
    def cookies(self):
        return self.get_cookies()

    @property
    def reason(self) -> str:
        return http.HTTPStatus(self.status).phrase

    def get_cookies(self):
        cdef bytes value
        cdef Cookie cookie
        cdef dict cookies
        cdef list set_cookies_headers

        cookies = {}
        set_cookies_headers = self.get_headers(b'set-cookie')
        if set_cookies_headers:
            for value in set_cookies_headers:
                cookie = parse_cookie(value)
                cookies[cookie.name] = cookie
        return cookies

    def get_cookie(self, str name):
        cdef bytes value
        cdef list set_cookies_headers = self.get_headers(b'set-cookie')

        if set_cookies_headers:
            for value in set_cookies_headers:
                cookie = parse_cookie(value)
                if cookie.name == name:
                    return cookie

        return None

    def set_cookie(self, Cookie cookie):
        self._raw_headers.append((b'set-cookie', write_cookie_for_response(cookie)))

    def set_cookies(self, list cookies):
        cdef Cookie cookie
        for cookie in cookies:
            self.set_cookie(cookie)

    def unset_cookie(self, str name):
        self.set_cookie(
            Cookie(
                name,
                '',
                utcnow() - timedelta(days=365)
            )
        )

    def remove_cookie(self, str name):
        cdef list to_remove = []
        cdef tuple value
        cdef list set_cookies_headers = self.get_headers_tuples(b'set-cookie')

        if set_cookies_headers:
            for value in set_cookies_headers:
                cookie = parse_cookie(value[1])
                if cookie.name == name:
                    to_remove.append(value)

        self.remove_headers(to_remove)

    cpdef bint is_redirect(self):
        return self.status in {301, 302, 303, 307, 308}

    cpdef void reset(self):
        self.status = 200
        self.state = None
        self.context = None
        self.scope_protocol = None
        self._form_data = None
        self._headers = None
        self._raw_headers = []
        if self.content is not None:
            self.content.dispose()
            self.content = None

    async def raise_for_status(self):
        if not (200 <= self.status < 300):
            raise FailedRequestError(self.status, await self.text())


cdef list _REQ_FREELIST = []
cdef list _RESP_FREELIST = []
cdef int _MAX_FREELIST_CAPACITY = 512


cpdef Request acquire_request(str method, object path, object raw_query, list headers, object scope):
    cdef Request req
    cdef str interned_method = intern_method_str(method)
    cdef list processed_headers
    if headers is None:
        processed_headers = None
    elif not headers:
        processed_headers = []
    else:
        processed_headers = [(intern_header_name_bytes(h[0]), h[1]) if isinstance(h, tuple) and len(h) == 2 and isinstance(h[0], bytes) else h for h in headers]

    if _REQ_FREELIST:
        req = <Request>_REQ_FREELIST.pop()
        req.method = interned_method
        req._path = path
        req._raw_query = raw_query
        req._raw_headers = processed_headers
        req.scope = scope
        req.scope_protocol = None
        req.content = None
        req._url = None
        req.route_values = None
        return req
    req = Request.__new__(Request)
    req.method = interned_method
    req._path = path
    req._raw_query = raw_query
    req._raw_headers = processed_headers
    req.scope = scope
    req.scope_protocol = None
    req.content = None
    req._url = None
    req.route_values = None
    return req


cpdef void release_request(Request request):
    if request is None:
        return
    if len(_REQ_FREELIST) < _MAX_FREELIST_CAPACITY:
        request.reset()
        _REQ_FREELIST.append(request)


cpdef Response acquire_response(int status=200, list headers=None, Content content=None):
    cdef Response resp
    if _RESP_FREELIST:
        resp = <Response>_RESP_FREELIST.pop()
        resp.status = status
        resp._raw_headers = headers if headers is not None else []
        resp.content = content
        return resp
    return Response(status, headers, content)


cpdef void release_response(Response response):
    if response is None:
        return
    if len(_RESP_FREELIST) < _MAX_FREELIST_CAPACITY:
        response.reset()
        _RESP_FREELIST.append(response)


cpdef bint is_cors_request(Request request):
    return bool(request.get_first_header(b"Origin"))


cpdef bint is_cors_preflight_request(Request request):
    if request.method != "OPTIONS" or not is_cors_request(request):
        return False

    next_request_method = request.get_first_header(
        b"Access-Control-Request-Method"
    )

    return bool(next_request_method)


cdef bytes ensure_bytes(value):
    if isinstance(value, str):
        return value.encode()
    if isinstance(value, bytes):
        return value
    raise ValueError("Input value must be bytes or str")


cpdef URL get_request_absolute_url(Request request):
    if request.url.is_absolute:
        # outgoing request
        return request.url

    # incoming request
    return build_absolute_url(
        ensure_bytes(request.scheme),
        ensure_bytes(request.host),
        ensure_bytes(request.base_path),
        request._path
    )


cpdef URL get_absolute_url_to_path(Request request, str path):
    return build_absolute_url(
        ensure_bytes(request.scheme),
        ensure_bytes(request.host),
        ensure_bytes(request.base_path),
        ensure_bytes(path)
    )
