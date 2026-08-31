# cython: language_level=3, embedsignature=True
# Copyright (C) 2018-present Roberto Prevato
#
# This module is part of Dreaming Electric Sheep and is released under
# the MIT License https://opensource.org/licenses/MIT


cdef class Header:
    cdef readonly object name
    cdef readonly object value


cdef class Headers:
    cdef readonly list values

    cpdef tuple keys(self)

    cpdef Headers clone(self)

    cpdef tuple get(self, object name)

    cpdef list get_tuples(self, object name)

    cpdef void add(self, object name, object value)

    cpdef void set(self, object name, object value)

    cpdef object get_single(self, object name)

    cpdef object get_first(self, object name)

    cpdef void remove(self, object key)

    cpdef void merge(self, list values)

    cpdef bint contains(self, object key)
