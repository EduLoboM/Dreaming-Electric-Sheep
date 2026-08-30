# cython: language_level=3

cdef extern from "fast_parse.h":
    ctypedef enum des_err:
        DES_OK
        DES_ERR_NOMEM
        DES_ERR_BAD_ARG
        DES_ERR_OVERFLOW
        DES_ERR_SIMD_UNSUPPORTED
        DES_ERR_ARENA_EXHAUSTED
        DES_ERR_PARSE_FAILED
        DES_ERR_NOT_FOUND

cdef class DesCoreError(Exception):
    cdef public int error_code
    cdef public str message

cdef class MemoryExhaustedError(DesCoreError):
    pass

cdef class ParseError(DesCoreError):
    pass

cdef class SimdUnsupportedError(DesCoreError):
    pass

cdef class InvalidArgumentError(DesCoreError):
    pass

cpdef void check_des_err(int code, str msg=*) except *
