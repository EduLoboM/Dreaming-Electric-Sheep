# cython: language_level=3, embedsignature=True
# Copyright (C) 2018-present Roberto Prevato
#
# This module is part of Dreaming Electric Sheep and is released under
# the MIT License https://opensource.org/licenses/MIT

from .contents cimport Content, parse_www_form_urlencoded
from .cookies cimport (
    Cookie,
    datetime_to_cookie_format,
    parse_cookie,
    write_cookie_for_response,
)
from .exceptions cimport BadRequestFormat
from .headers cimport Headers
from .url cimport URL


cdef class Message:
    cdef list _raw_headers
    cdef public Headers _headers
    cdef public Content content
    cdef public object scope_protocol
    cdef public object _form_data
    cdef public object context
    cdef object __weakref__

    cpdef list get_headers(self, object key)
    cpdef object get_first_header(self, object key)
    cpdef object get_single_header(self, object key)
    cpdef void remove_header(self, object key)
    cdef bint _has_header(self, object key)
    cpdef bint has_header(self, object key)
    cdef void _add_header(self, object key, object value)
    cdef void _add_header_if_missing(self, object key, object value)
    cpdef void add_header(self, object key, object value)
    cpdef void set_header(self, object key, object value)
    cpdef object content_type(self)

    cdef void remove_headers(self, list headers)
    cdef list get_headers_tuples(self, object key)
    cdef void init_prop(self, str name, object value)

    cpdef Message with_content(self, Content content)
    cpdef bint has_body(self)
    cpdef bint declares_content_type(self, object type)
    cpdef bint declares_json(self)
    cpdef bint declares_xml(self)


cdef extern from "fast_parse.h":
    ctypedef enum des_err:
        DES_OK

cdef extern from "scratchpad.h":
    ctypedef struct ScratchpadArena:
        char *buffer
        size_t capacity
        size_t offset
        int is_dynamic
    des_err scratchpad_init(ScratchpadArena *arena, size_t capacity)
    des_err scratchpad_alloc(ScratchpadArena *arena, size_t size, size_t alignment, void **out_ptr)
    void scratchpad_reset(ScratchpadArena *arena)
    void scratchpad_destroy(ScratchpadArena *arena)


cdef class Request(Message):
    cdef public str method
    cdef public URL _url
    cdef public object _path
    cdef public object _raw_query
    cdef public object route_values
    cdef public object scope
    cdef public object _user
    cdef public object _di_scope
    cdef public object state
    cdef public object _session
    cdef public str _base_path
    cdef public str _original_client_ip
    cdef public str _host
    cdef public str _scheme
    cdef public object _context
    cdef public object services
    cdef public object _is_disconnected
    cdef ScratchpadArena _arena
    cdef bint _arena_initialized

    cpdef bint expect_100_continue(self)
    cpdef void reset(self)
    cdef void *alloc_scratchpad(self, size_t size, size_t alignment=*)


cdef class Response(Message):
    cdef public int status
    cdef public object state
    cdef public object _context

    cpdef bint is_redirect(self)
    cpdef void reset(self)


cpdef Request acquire_request(str method, object path, object raw_query, list headers, object scope)
cpdef void release_request(Request request)

cpdef Response acquire_response(int status=*, list headers=*, Content content=*)
cpdef void release_response(Response response)


cpdef bint method_without_body(str method)

cpdef bint is_cors_request(Request request)

cpdef bint is_cors_preflight_request(Request request)

cpdef URL get_request_absolute_url(Request request)

cpdef URL get_absolute_url_to_path(Request request, str path)

cdef bytes ensure_bytes(value)
