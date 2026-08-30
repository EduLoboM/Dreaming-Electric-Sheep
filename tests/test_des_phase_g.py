"""
Tests for Phase G: Free-threaded / NoGIL safe freelists, Router.freeze(), and typed diagnostic error codes.
"""
import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from dreaming_electric_sheep import (
    Request,
    Response,
    Router,
    DesCoreError,
    MemoryExhaustedError,
    ParseError,
    SimdUnsupportedError,
    InvalidArgumentError,
)
from dreaming_electric_sheep.core_errors import HeaderError
from dreaming_electric_sheep.messages import (
    acquire_request,
    release_request,
    acquire_response,
    release_response,
)


def test_typed_diagnostic_error_codes():
    """Verify diagnostic error code tags across the exception hierarchy."""
    base = DesCoreError("base error", 0)
    assert base.diagnostic_code == "DES_E000"
    assert "[DES_E000:0]" in str(base)

    hdr = HeaderError("invalid header format")
    assert hdr.diagnostic_code == "DES_E001"
    assert "[DES_E001:1]" in str(hdr)

    mem = MemoryExhaustedError("arena limit reached")
    assert mem.diagnostic_code == "DES_E002"
    assert "[DES_E002:5]" in str(mem)

    simd = SimdUnsupportedError("AVX2 missing")
    assert simd.diagnostic_code == "DES_E003"
    assert "[DES_E003:4]" in str(simd)

    parse = ParseError("malformed integer")
    assert parse.diagnostic_code == "DES_E004"
    assert "[DES_E004:6]" in str(parse)

    arg = InvalidArgumentError("null pointer")
    assert arg.diagnostic_code == "DES_E005"
    assert "[DES_E005:2]" in str(arg)


def test_free_threaded_freelist_concurrent_stress():
    """
    Stress test acquire_request and acquire_response across multiple concurrent threads
    to verify thread-safety and lack of contention or state corruption in NoGIL / free-threaded mode.
    """
    errors = []

    def worker_thread(thread_id: int):
        try:
            scope = {"type": "http", "method": "GET", "path": f"/thread/{thread_id}"}
            for i in range(500):
                req = acquire_request(
                    "GET",
                    f"/thread/{thread_id}/item/{i}".encode(),
                    b"",
                    [(b"Host", b"localhost"), (b"X-Worker", str(thread_id).encode())],
                    scope,
                )
                assert req.method == "GET"
                assert req._path == f"/thread/{thread_id}/item/{i}".encode()

                resp = acquire_response(200, [(b"Content-Type", b"text/plain")])
                assert resp.status == 200

                release_response(resp)
                release_request(req)
        except Exception as e:
            errors.append(e)

    num_threads = 8
    threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Thread-local freelist encountered errors under concurrent load: {errors}"


def test_router_freeze():
    """Verify Router.freeze() marks the routing table immutable for O(1) concurrent dispatch."""
    router = Router()

    async def home_handler():
        return "ok"

    async def user_handler():
        return "user"

    router.add_get("/", home_handler)
    router.add_get("/users/{user_id}", user_handler)

    assert not getattr(router, "_frozen", False)
    router.freeze()
    assert getattr(router, "_frozen", False) is True

    # Calling freeze again is idempotent
    router.freeze()
    assert getattr(router, "_frozen", False) is True
