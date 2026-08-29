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

import httptools
from urllib.parse import urlparse
from libc.stdint cimport int64_t, uint32_t

cdef extern from "simd_ops.h":
    int simd_validate_url_ascii(const char *buffer, size_t length)
    int64_t simd_find_path_separator(const char *buffer, size_t length, size_t start_pos)


cdef class InvalidURL(Exception):
    def __init__(self, str message):
        super().__init__(message)


cdef inline valid_schema(bytes schema):
    if schema and schema != b'https' and schema != b'http':
        raise InvalidURL(f'Expected http or https schema; got instead {schema.decode()}')


cdef class URL:

    def __init__(self, bytes value):
        cdef bytes schema
        cdef object port
        if not value:
            raise InvalidURL("Input empty or null.")
        try:
            # if the value starts with a dot, prepend a slash;
            # urllib.parse urlparse handles those, while httptools raises
            # an exception
            if value and value[0] == 46:
                value = b"/" + value

            parsed = httptools.parse_url(value)
            schema = parsed.schema
            valid_schema(schema)
            self.value = value or b''
            self.schema = schema
            self.host = parsed.host
            self.port = parsed.port or 0
            self.path = parsed.path
            self.query = parsed.query
            self.fragment = parsed.fragment
            self.is_absolute = parsed.schema is not None
        except Exception as exc:
            raise InvalidURL(f'The value cannot be parsed as URL ({value.decode()}): {exc}')

    def __repr__(self):
        return f'<URL {self.value}>'

    def __str__(self):
        return self.value.decode()

    cpdef URL join(self, URL other):
        if other.is_absolute:
            raise ValueError(f'Cannot concatenate to an absolute URL ({self.value} + {other.value})')
        if self.query or self.fragment:
            raise ValueError('Cannot concatenate a URL with query or fragment to another URL portion')
        first_part = self.value
        other_part = other.value
        if first_part and other_part and first_part.endswith(b"/") and other_part.startswith(b"/"):
            return URL(first_part[:len(first_part) - 1] + other_part)
        return URL(first_part + other_part)

    cpdef URL base_url(self):
        if not self.is_absolute:
            raise ValueError('This URL is relative. Cannot extract a base URL (without path).')
        cdef bytes base_url

        base_url = self.schema + b'://' + self.host

        if self.port != 0:
            if (self.schema == b'http' and self.port != 80) or (self.schema == b'https' and self.port != 443):
                base_url = base_url + b':' + str(self.port).encode()

        return URL(base_url)

    cpdef URL with_host(self, bytes host):
        cdef bytes value
        if not self.is_absolute:
            raise ValueError('This URL is not absolute.')
        value = self.schema + b'://' + host + self.path
        if self.query:
            value = value + b'?' + self.query
        if self.fragment:
            value = value + b'#' + self.fragment
        return URL(value)

    cpdef URL with_query(self, bytes query):
        cdef bytes value
        if not self.is_absolute:
            value = self.path
        else:
            value = self.schema + b'://' + self.host + self.path
        if query:
            value = value + b'?' + query
        if self.fragment:
            value = value + b'#' + self.fragment
        return URL(value)

    cpdef URL with_scheme(self, bytes schema):
        cdef bytes value
        if not self.is_absolute:
            raise ValueError('This URL is not absolute.')
        valid_schema(schema)
        value = schema + b'://' + self.host + self.path
        if self.query:
            value = value + b'?' + self.query
        if self.fragment:
            value = value + b'#' + self.fragment
        return URL(value)

    def __add__(self, other):
        if isinstance(other, bytes):
            return self.join(URL(other))

        if isinstance(other, URL):
            return self.join(other)
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, URL):
            return self.value == other.value
        return NotImplemented


cpdef URL build_absolute_url(
    bytes scheme,
    bytes host,
    bytes base_path,
    bytes path
):
    if not path:
        path = b'/'

    if not path.startswith(b'/'):
        path = b'/' + path

    if base_path:
        if not base_path.startswith(b'/'):
            base_path = b'/' + base_path

        if base_path.endswith(b'/'):
            base_path = base_path[:len(base_path) - 1]

        path = base_path + path

    return URL(scheme + b'://' + host + path)


cpdef str join_prefix(
    str prefix,
    str path
):
    if not prefix:
        return path

    if not prefix.startswith("/"):
        prefix = "/" + prefix

    if not path:
        return prefix + "/"

    if prefix.endswith("/") and path.startswith("/"):
        return prefix + path[1:]

    if not prefix.endswith("/") and not path.startswith("/"):
        return prefix + "/" + path

    return prefix + path
