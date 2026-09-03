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

from collections.abc import Mapping, MutableSequence
from cpython.object cimport PyObject
from cpython.bytes cimport PyBytes_AS_STRING, PyBytes_GET_SIZE, PyBytes_FromStringAndSize, PyBytes_CheckExact
from cpython.unicode cimport PyUnicode_CheckExact

import sys

cdef extern from "simd_ops.h":
    void simd_lowercase_ascii(const char *src, char *dst, size_t length)
    int simd_is_ascii_lowercase(const char *s, size_t length)

cdef extern from "interning.h":
    PyObject *get_interned_header_name_bytes(const char *name_str, size_t len)
    PyObject *get_interned_header_name_str(const char *name_str, size_t len)
    PyObject *get_interned_content_type_bytes(const char *type_str, size_t len)

cdef inline bytes simd_lower_bytes(bytes name):
    if name is None:
        return None
    cdef char *raw = PyBytes_AS_STRING(name)
    cdef Py_ssize_t size = PyBytes_GET_SIZE(name)
    if size == 0:
        return name
    if simd_is_ascii_lowercase(raw, <size_t>size):
        return name
    cdef bytes lowered = PyBytes_FromStringAndSize(NULL, size)
    cdef char *dst = PyBytes_AS_STRING(lowered)
    simd_lowercase_ascii(raw, dst, <size_t>size)
    return lowered

cpdef bytes intern_header_name_bytes(bytes name):
    if name is None:
        return None
    cdef char *raw = PyBytes_AS_STRING(name)
    cdef Py_ssize_t size = PyBytes_GET_SIZE(name)
    cdef PyObject *interned = get_interned_header_name_bytes(raw, <size_t>size)
    if interned != NULL:
        return <bytes><object>interned
    if not simd_is_ascii_lowercase(raw, <size_t>size):
        name = simd_lower_bytes(name)
        raw = PyBytes_AS_STRING(name)
        interned = get_interned_header_name_bytes(raw, <size_t>size)
        if interned != NULL:
            return <bytes><object>interned
    return name

cdef dict _KNOWN_HEADERS_STR = {
    "content-type": "content-type",
    "content-length": "content-length",
    "host": "host",
    "cookie": "cookie",
    "set-cookie": "set-cookie",
    "accept": "accept",
    "accept-encoding": "accept-encoding",
    "accept-language": "accept-language",
    "user-agent": "user-agent",
    "server": "server",
    "date": "date",
    "connection": "connection",
    "transfer-encoding": "transfer-encoding",
    "authorization": "authorization",
    "location": "location",
    "etag": "etag",
    "if-none-match": "if-none-match",
    "origin": "origin",
    "access-control-allow-origin": "access-control-allow-origin",
    "access-control-request-method": "access-control-request-method",
    "hx-request": "hx-request",
    "hx-target": "hx-target",
    "hx-trigger": "hx-trigger",
    "hx-current-url": "hx-current-url",
    "hx-prompt": "hx-prompt",
}

cpdef str intern_header_name_str(object name):
    if name is None:
        return None
    cdef str s_name = name if PyUnicode_CheckExact(name) else str(name)
    cdef str cached = _KNOWN_HEADERS_STR.get(s_name)
    if cached is not None:
        return cached
    cdef str lower_name = s_name.lower()
    cached = _KNOWN_HEADERS_STR.get(lower_name)
    if cached is not None:
        return cached
    return sys.intern(lower_name)


cdef inline bint _header_name_matches(object h_name, bytes low_name_bytes, str low_name_str):
    if low_name_str is not None and (PyUnicode_CheckExact(h_name) or isinstance(h_name, str)):
        return h_name is low_name_str or (<str>h_name).lower() == low_name_str
    elif low_name_bytes is not None and PyBytes_CheckExact(h_name):
        return h_name is low_name_bytes or (<bytes>h_name).lower() == low_name_bytes
    elif low_name_str is not None and PyBytes_CheckExact(h_name):
        return (<bytes>h_name).lower() == (<str>low_name_str).encode("latin-1")
    elif low_name_bytes is not None and (PyUnicode_CheckExact(h_name) or isinstance(h_name, str)):
        return (<str>h_name).lower() == (<bytes>low_name_bytes).decode("latin-1")
    return False

cdef inline object _convert_header_val_matching_key(object val, bint caller_asked_bytes):
    if val is None:
        return None
    if caller_asked_bytes:
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

cdef class Header:

    def __init__(self, object name, object value):
        if PyBytes_CheckExact(name):
            self.name = intern_header_name_bytes(<bytes>name)
        elif PyUnicode_CheckExact(name) or isinstance(name, str):
            self.name = intern_header_name_str(name)
        else:
            self.name = name
        self.value = value

    def __repr__(self):
        return f'<Header {self.name}: {self.value}>'

    def __iter__(self):
        yield self.name
        yield self.value

    def __eq__(self, other):
        if isinstance(other, Header):
            return (other.name is self.name or other.name == self.name or str(other.name).lower() == str(self.name).lower()) and other.value == self.value
        return NotImplemented


cdef class Headers:

    def __init__(self, list values = None):
        if values is None:
            values = []
        self.values = values

    cpdef tuple get(self, object name):
        cdef list results = []
        cdef tuple header
        cdef bytes low_b = None
        cdef str low_s = None
        cdef bint is_bytes = PyBytes_CheckExact(name)

        if is_bytes:
            low_b = intern_header_name_bytes(simd_lower_bytes(<bytes>name))
        elif PyUnicode_CheckExact(name) or isinstance(name, str):
            low_s = intern_header_name_str(name)
        else:
            low_s = intern_header_name_str(str(name))

        for header in self.values:
            if _header_name_matches(header[0], low_b, low_s):
                results.append(_convert_header_val_matching_key(header[1], is_bytes))
        return tuple(results)

    cpdef list get_tuples(self, object name):
        cdef list results = []
        cdef tuple header
        cdef bytes low_b = None
        cdef str low_s = None

        if PyBytes_CheckExact(name):
            low_b = intern_header_name_bytes(simd_lower_bytes(<bytes>name))
        elif PyUnicode_CheckExact(name) or isinstance(name, str):
            low_s = intern_header_name_str(name)
        else:
            low_s = intern_header_name_str(str(name))

        for header in self.values:
            if _header_name_matches(header[0], low_b, low_s):
                results.append(header)
        return results

    cpdef object get_first(self, object key):
        cdef tuple header
        cdef bytes low_b = None
        cdef str low_s = None
        cdef bint is_bytes = PyBytes_CheckExact(key)

        if is_bytes:
            low_b = intern_header_name_bytes(simd_lower_bytes(<bytes>key))
        elif PyUnicode_CheckExact(key) or isinstance(key, str):
            low_s = intern_header_name_str(key)
        else:
            low_s = intern_header_name_str(str(key))

        for header in self.values:
            if _header_name_matches(header[0], low_b, low_s):
                return _convert_header_val_matching_key(header[1], is_bytes)
        return None

    cpdef object get_single(self, object key):
        cdef tuple results = self.get(key)
        if len(results) > 1:
            raise ValueError('Headers contains more than one header with the given key')
        if len(results) < 1:
            raise ValueError('Headers does not contain one header with the given key')
        return results[0]

    cpdef void merge(self, list values):
        cdef tuple header
        for header in values:
            if header is None:
                continue
            self.values.append(header)

    def update(self, dict values):
        for key, value in values.items():
            self[key] = value

    def items(self):
        yield from self.values

    cpdef Headers clone(self):
        cdef list values = []
        cdef bytes name, value
        for name, value in self.values:
            values.append((name, value))
        return Headers(values)

    def add_many(self, values):
        if isinstance(values, MutableSequence):
            for item in values:
                self.add(*item)
            return

        if isinstance(values, Mapping):
            for key, value in values.items():
                self.add(key, value)
            return
        raise ValueError('values must be dict[bytes, bytes] or list[Header]')

    @staticmethod
    def _add_to_instance(instance, other):
        if isinstance(other, Headers):
            for value in other:
                instance.add(*value)
            return instance

        if isinstance(other, Header):
            instance.add(other.name, other.value)
            return instance

        if isinstance(other, tuple):
            if len(other) != 2:
                raise ValueError(f'Cannot add, an invalid tuple {str(other)}.')
            instance.add(*other)
            return instance

        if isinstance(other, MutableSequence):
            for value in other:
                if isinstance(value, tuple) and len(value) == 2:
                    instance.add(*value)
                else:
                    raise ValueError(f'The sequence contains invalid elements: '
                                     f'cannot add {str(value)} to {instance.__class__.__name__}')
            return instance

        return NotImplemented

    def __add__(self, other):
        return self._add_to_instance(self.clone(), other)

    def __radd__(self, other):
        return self._add_to_instance(self.clone(), other)

    def __iadd__(self, other):
        return self._add_to_instance(self, other)

    def __iter__(self):
        yield from self.values

    def __setitem__(self, object key, object value):
        self.set(key, value)

    def __getitem__(self, object item):
        return self.get(item)

    cpdef tuple keys(self):
        cdef list results = []
        for pair in self.values:
            if pair[0] not in results:
                results.append(pair[0])
        return tuple(results)

    cpdef void add(self, object name, object value):
        if PyBytes_CheckExact(name):
            self.values.append((intern_header_name_bytes(<bytes>name), value))
        elif PyUnicode_CheckExact(name) or isinstance(name, str):
            self.values.append((intern_header_name_str(name), value))
        else:
            self.values.append((name, value))

    cpdef void set(self, object name, object value):
        if self.contains(name):
            self.remove(name)
        self.add(name, value)

    cpdef void remove(self, object key):
        cdef tuple item
        cdef list to_remove = []
        cdef bytes low_b = None
        cdef str low_s = None

        if PyBytes_CheckExact(key):
            low_b = intern_header_name_bytes(simd_lower_bytes(<bytes>key))
        elif PyUnicode_CheckExact(key) or isinstance(key, str):
            low_s = intern_header_name_str(key)
        else:
            low_s = intern_header_name_str(str(key))

        for item in self.values:
            if _header_name_matches(item[0], low_b, low_s):
                to_remove.append(item)

        for item in to_remove:
            self.values.remove(item)

    cpdef bint contains(self, object key):
        cdef bytes low_b = None
        cdef str low_s = None

        if PyBytes_CheckExact(key):
            low_b = intern_header_name_bytes(simd_lower_bytes(<bytes>key))
        elif PyUnicode_CheckExact(key) or isinstance(key, str):
            low_s = intern_header_name_str(key)
        else:
            low_s = intern_header_name_str(str(key))

        for item in self.values:
            if _header_name_matches(item[0], low_b, low_s):
                return True
        return False

    def __delitem__(self, object key):
        self.remove(key)

    def __contains__(self, object key):
        return self.contains(key)

    def __repr__(self):
        return f'<Headers {self.values}>'


# Pre-allocated static headers singletons for zero-allocation outbound dispatch
STATIC_JSON_HEADERS = [(b"content-type", b"application/json")]
STATIC_TEXT_HEADERS = [(b"content-type", b"text/plain; charset=utf-8")]
STATIC_HTML_HEADERS = [(b"content-type", b"text/html; charset=utf-8")]
STATIC_NOT_FOUND_HEADERS = [(b"content-type", b"text/plain")]
