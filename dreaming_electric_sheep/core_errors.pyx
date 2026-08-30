# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: language_level=3

"""
Typed Python exception hierarchy for Dreaming Electric Sheep C-core results (des_err).
"""

cdef class DesCoreError(Exception):
    def __init__(self, str message, int error_code = 0):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __repr__(self):
        return f"{self.__class__.__name__}(code={self.error_code}, {self.message!r})"

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


cdef class MemoryExhaustedError(DesCoreError):
    """Raised when memory allocation fails or scratchpad arena capacity is exhausted."""
    pass


cdef class ParseError(DesCoreError):
    """Raised when parsing headers, integers, or tokens from a buffer fails or overflows."""
    pass


cdef class SimdUnsupportedError(DesCoreError):
    """Raised when required SIMD instruction sets (AVX-512, AVX2, NEON) are unavailable."""
    pass


cdef class InvalidArgumentError(DesCoreError):
    """Raised when an invalid argument or null pointer is passed to a C core API."""
    pass


cpdef void check_des_err(int code, str msg=None) except *:
    """
    Checks a C des_err result code and raises the corresponding typed Python exception
    if the code is not DES_OK. Zero-overhead when code is DES_OK.
    """
    if code == 0:
        return
    if code == 1 or code == 5:
        raise MemoryExhaustedError(msg or "Memory arena or heap allocation exhausted", code)
    elif code == 6 or code == 3:
        raise ParseError(msg or "Parsing buffer failed or integer overflowed", code)
    elif code == 4:
        raise SimdUnsupportedError(msg or "CPU does not support required SIMD instruction set", code)
    elif code == 2:
        raise InvalidArgumentError(msg or "Invalid argument or null pointer in C core", code)
    else:
        raise DesCoreError(msg or f"Unknown core error code: {code}", code)
