"""
Tests for Runtime SIMD CPUID dispatch and C core acceleration kernels.
"""

import platform
import sys

import pytest

from dreaming_electric_sheep import _des_core
from dreaming_electric_sheep.cli.doctor import run_doctor
from dreaming_electric_sheep.headers import Header, Headers
from dreaming_electric_sheep.messages import Request, Response


def test_simd_isa_runtime_dispatch_token():
    """Verify get_simd_isa_info returns valid token and never false SCALAR on x86_64 Linux."""
    isa = _des_core.get_simd_isa_info()
    assert isa in {"AVX2", "SSE2", "NEON", "SCALAR"}

    arch = platform.machine().lower()
    # MSVC does not support __builtin_cpu_supports; SCALAR is expected on Windows.
    if arch in {"x86_64", "amd64"} and sys.platform != "win32":
        assert isa in {
            "AVX2",
            "SSE2",
        }, f"Expected AVX2 or SSE2 on x86_64 Linux, got: {isa}"


def test_simd_doctor_diagnostics_report():
    """Verify des doctor correctly surfaces the active SIMD runtime ISA."""
    report = run_doctor()
    assert report["c_core_loaded"] is True
    assert report["simd_isa"] in {"AVX2", "SSE2", "NEON", "SCALAR"}
    if platform.machine().lower() in {"x86_64", "amd64"} and sys.platform != "win32":
        assert report["simd_isa"] in {"AVX2", "SSE2"}


def test_simd_header_lowercasing_correctness():
    """Verify SIMD header lowercasing across small, 32-byte, and multi-vector strings."""
    test_cases = [
        b"Content-Type",
        b"X-CUSTOM-HEADER-LONG-NAME-THAT-EXCEEDS-THIRTY-TWO-BYTES-FOR-AVX2",
        b"Host",
        b"ACCEPT-ENCODING",
        b"USER-AGENT: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        b"already-lowercase-header-value",
        b"MIXED-CaSe-HeAdEr-VaLuE-1234567890-!@#$%^&*()_+",
    ]

    for raw in test_cases:
        h = Header(raw, b"value")
        expected_lower = raw.lower()
        assert (
            h.name == expected_lower
        ), f"Failed lowercasing for {raw!r}: expected {expected_lower!r}, got {h.name!r}"


def test_simd_headers_lookup_and_interning():
    """Verify Headers.get, contains, and remove operate transparently through SIMD dispatch."""
    headers = Headers(
        [
            (b"Content-Type", b"application/json"),
            (b"X-REQUEST-ID", b"12345"),
            (b"X-VERY-LONG-HEADER-NAME-TESTING-VECTORIZED-LOOKUP", b"test-val"),
        ]
    )

    assert headers.get(b"content-type") == (b"application/json",)
    assert headers.get_first(b"CONTENT-TYPE") == b"application/json"
    assert headers.get(b"Content-Type") == (b"application/json",)
    assert b"x-request-id" in headers
    assert b"X-REQUEST-ID" in headers
    assert b"x-very-long-header-name-testing-vectorized-lookup" in headers

    headers.remove(b"X-REQUEST-ID")
    assert b"x-request-id" not in headers


def test_simd_routing_and_url_path_matching():
    """Verify URL routing and path separator parsing accelerated by SIMD."""
    from dreaming_electric_sheep.routing import CythonRadixRouter

    router = CythonRadixRouter()
    mock_route = object()
    router.add_route(
        b"GET", b"/api/v1/users/{user_id}/profile/settings", mock_route, ["user_id"]
    )

    match = router.get_match(b"GET", b"/api/v1/users/42/profile/settings")
    assert match is not None
    assert match[0] is mock_route
    assert match[1]["user_id"] == "42"


def test_cross_module_intern_table_identity():
    """Verify static intern table is a true shared singleton between headers, messages, and core."""
    h = Header(b"content-type", b"application/json")
    req = Request("GET", b"/test", [(b"content-type", b"application/json")])

    req_header_name = req.headers.values[0][0]
    assert h.name == req_header_name
    assert (
        h.name is req_header_name
    ), "Header name bytes should be identical interned PyObject pointers across modules"
