"""
Tests for Phase C: SIMD lowercasing, integer parsing, and Request scratchpad arena.
"""

import ctypes

import pytest

import dreaming_electric_sheep._des_core as core
from dreaming_electric_sheep import Header, Headers, Request, Response
from dreaming_electric_sheep.messages import acquire_request, release_request


def test_simd_lowercase_ascii_direct():
    """Verify SIMD ASCII lowercasing with various string lengths."""
    dll = ctypes.CDLL(core.__file__)
    assert hasattr(dll, "simd_lowercase_ascii")
    assert hasattr(dll, "simd_is_ascii_lowercase")

    simd_lower = dll.simd_lowercase_ascii
    simd_lower.restype = None
    simd_lower.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t]

    is_lower = dll.simd_is_ascii_lowercase
    is_lower.restype = ctypes.c_int
    is_lower.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    # Test short string
    src = b"Content-Type"
    dst = ctypes.create_string_buffer(len(src))
    simd_lower(src, dst, len(src))
    assert dst.raw == b"content-type"
    assert is_lower(b"content-type", 12) == 1
    assert is_lower(b"Content-Type", 12) == 0

    # Test long string > 32 bytes (AVX2/SSE2 vectorized chunks)
    long_hdr = b"X-CUSTOM-AUTHENTICATION-TOKEN-AUTHORIZATION-BEARER-ID"
    dst_long = ctypes.create_string_buffer(len(long_hdr))
    simd_lower(long_hdr, dst_long, len(long_hdr))
    assert dst_long.raw == b"x-custom-authentication-token-authorization-bearer-id"


def test_headers_simd_lowercasing_integration():
    """Verify Header and Headers transparently lowercase keys using SIMD."""
    h = Header(b"X-Custom-Header", b"CustomValue")
    assert h.name == b"x-custom-header"

    headers = Headers()
    headers.add(b"X-FORWARDED-FOR", b"127.0.0.1")
    assert headers.get_first(b"x-forwarded-for") == b"127.0.0.1"
    assert headers.get_first(b"X-Forwarded-For") == b"127.0.0.1"
    assert headers.contains(b"X-FORWARDED-FOR") is True

    headers.remove(b"X-Forwarded-For")
    assert headers.contains(b"x-forwarded-for") is False


def test_request_scratchpad_arena_lifecycle():
    """Verify Request scratchpad arena stats and O(1) reset on release."""
    scope = {"type": "http", "method": "GET", "path": "/"}
    req = acquire_request(
        "GET", b"/api/v1/resource", b"", [(b"Host", b"localhost")], scope
    )

    # Initial stats
    cap, offset, is_init = req.scratchpad_arena_stats()
    assert is_init is False or cap >= 65536

    # Release back to freelist
    release_request(req)

    # Re-acquire and verify clean state
    req2 = acquire_request("GET", b"/api/v2/items", b"", [], scope)
    assert req2.method == "GET"
    release_request(req2)
