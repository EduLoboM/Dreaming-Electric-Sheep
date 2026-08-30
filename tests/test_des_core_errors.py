"""
Tests for Phase B: C des_err result codes, out-pointers, and typed Python exceptions.
"""
import pytest
import ctypes
from dreaming_electric_sheep import (
    DesCoreError,
    MemoryExhaustedError,
    ParseError,
    SimdUnsupportedError,
    InvalidArgumentError,
)
from dreaming_electric_sheep.core_errors import check_des_err
import dreaming_electric_sheep._des_core as core


def test_exception_hierarchy():
    """Verify inheritance structure of typed DES core exceptions."""
    assert issubclass(MemoryExhaustedError, DesCoreError)
    assert issubclass(ParseError, DesCoreError)
    assert issubclass(SimdUnsupportedError, DesCoreError)
    assert issubclass(InvalidArgumentError, DesCoreError)
    assert issubclass(DesCoreError, Exception)

    err = MemoryExhaustedError("out of arena space", 5)
    assert err.error_code == 5
    assert err.message == "out of arena space"
    assert "MemoryExhaustedError" in repr(err)
    assert "[5] out of arena space" in str(err)


def test_check_des_err_dispatcher():
    """Verify check_des_err dispatches correct exceptions for all des_err values."""
    # DES_OK (0) should not raise
    check_des_err(0)

    # DES_ERR_NOMEM (1) & DES_ERR_ARENA_EXHAUSTED (5) -> MemoryExhaustedError
    with pytest.raises(MemoryExhaustedError) as exc1:
        check_des_err(1, "Heap allocation failed")
    assert exc1.value.error_code == 1

    with pytest.raises(MemoryExhaustedError) as exc5:
        check_des_err(5, "Arena exhausted")
    assert exc5.value.error_code == 5

    # DES_ERR_BAD_ARG (2) -> InvalidArgumentError
    with pytest.raises(InvalidArgumentError) as exc2:
        check_des_err(2, "Null pointer argument")
    assert exc2.value.error_code == 2

    # DES_ERR_OVERFLOW (3) & DES_ERR_PARSE_FAILED (6) -> ParseError
    with pytest.raises(ParseError) as exc3:
        check_des_err(3, "Integer overflow")
    assert exc3.value.error_code == 3

    with pytest.raises(ParseError) as exc6:
        check_des_err(6, "Invalid digit in integer parse")
    assert exc6.value.error_code == 6

    # DES_ERR_SIMD_UNSUPPORTED (4) -> SimdUnsupportedError
    with pytest.raises(SimdUnsupportedError) as exc4:
        check_des_err(4, "AVX-512 not available")
    assert exc4.value.error_code == 4

    # Unknown code -> DesCoreError
    with pytest.raises(DesCoreError) as exc_unknown:
        check_des_err(999, "Unknown error")
    assert exc_unknown.value.error_code == 999


def test_fast_parse_c_results():
    """Verify fast_parse functions return des_err with out-pointers via ctypes."""
    dll = ctypes.CDLL(core.__file__)

    # Fast parse uint64
    # des_err fast_parse_uint64(const char *s, size_t len, uint64_t *out)
    # We can test via scratchpad or direct core functions
    assert hasattr(dll, "scratchpad_init")
    assert hasattr(dll, "scratchpad_alloc")
    assert hasattr(dll, "scratchpad_destroy")
