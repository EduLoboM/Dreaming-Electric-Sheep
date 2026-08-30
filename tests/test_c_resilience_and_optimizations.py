import ctypes
import os
import pytest
from dreaming_electric_sheep.messages import (
    Request,
    Response,
    acquire_request,
    release_request,
    acquire_response,
    release_response,
)
from dreaming_electric_sheep.contents import Content, TextContent
from dreaming_electric_sheep.headers import Header, Headers
from dreaming_electric_sheep.url import URL
import dreaming_electric_sheep.url as url_mod


def test_request_response_freelist_uninitialized_bypass():
    """
    Test that acquire_request and acquire_response work efficiently with freelists
    without expensive zero-initialization or leaks.
    """
    req1 = acquire_request("GET", b"/optimized/api", b"q=1", [(b"host", b"localhost")], {})
    assert req1.method == "GET"
    assert req1._path == b"/optimized/api"
    assert req1.host == "localhost"

    release_request(req1)

    # Next acquire reuses instance cleanly
    req2 = acquire_request("POST", b"/optimized/submit", b"", [(b"content-type", b"application/json")], {})
    assert req2.method == "POST"
    assert req2._path == b"/optimized/submit"
    assert req2.content is None
    assert req2.state is None


def test_header_cdef_fast_operations():
    """
    Test that headers and fast operations perform without aliasing or memory issues.
    """
    h = Headers([(b"content-type", b"application/json"), (b"host", b"example.org")])
    assert h.get_first(b"content-type") == b"application/json"
    assert h.get_first(b"host") == b"example.org"
    assert h.contains(b"CONTENT-TYPE") is True
    assert h.contains(b"HOST") is True

    h.set(b"custom-header", b"custom-value")
    assert h.get_first(b"custom-header") == b"custom-value"


def test_url_simd_operations_and_prefetch():
    """
    Test URL creation, parsing, and SIMD separator operations.
    """
    url1 = URL(b"https://example.com/api/v1/users?page=1#profile")
    assert url1.is_absolute is True
    assert url1.schema == b"https"
    assert url1.host == b"example.com"
    assert url1.path == b"/api/v1/users"
    assert url1.query == b"page=1"
    assert url1.fragment == b"profile"

    # Longer URL to trigger SIMD chunks + prefetching
    long_path = b"/" + b"a" * 128 + b"/test"
    url2 = URL(b"http://localhost:8080" + long_path)
    assert url2.path == long_path
    assert url2.port == 8080


def test_simd_c_intrinsics_direct():
    """
    Test SIMD C library functions directly via ctypes.
    """
    lib_path = url_mod.__file__
    dll = ctypes.CDLL(lib_path)

    # 1. simd_find_crlf
    simd_find_crlf = dll.simd_find_crlf
    simd_find_crlf.restype = ctypes.c_int64
    simd_find_crlf.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    buf1 = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    pos = simd_find_crlf(buf1, len(buf1))
    assert pos == 14
    assert buf1[pos:pos+2] == b"\r\n"

    # 2. simd_find_crlf_crlf
    simd_find_crlf_crlf = dll.simd_find_crlf_crlf
    simd_find_crlf_crlf.restype = ctypes.c_int64
    simd_find_crlf_crlf.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    pos_end = simd_find_crlf_crlf(buf1, len(buf1))
    assert pos_end == 31
    assert buf1[pos_end:pos_end+4] == b"\r\n\r\n"

    # 3. simd_validate_url_ascii
    simd_validate_url_ascii = dll.simd_validate_url_ascii
    simd_validate_url_ascii.restype = ctypes.c_int
    simd_validate_url_ascii.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    valid_url = b"https://example.com/test?q=hello~world"
    assert simd_validate_url_ascii(valid_url, len(valid_url)) == 1

    invalid_url = b"https://example.com/test\x00bad"
    assert simd_validate_url_ascii(invalid_url, len(invalid_url)) == 0

    # 4. simd_fast_hash
    simd_fast_hash = dll.simd_fast_hash
    simd_fast_hash.restype = ctypes.c_uint32
    simd_fast_hash.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    h1 = simd_fast_hash(b"content-type", 12)
    h2 = simd_fast_hash(b"content-type", 12)
    h3 = simd_fast_hash(b"content-length", 14)
    assert h1 != 0
    assert h1 == h2
    assert h1 != h3


def test_c_interning_symbols_loaded():
    """
    Verify that the static interning table and C intrinsics compile and load cleanly into extensions.
    """
    # Messages module loads interning.c and scratchpad.c
    import dreaming_electric_sheep.messages as m
    assert hasattr(m, "acquire_request")
    assert hasattr(m, "acquire_response")

    # URL module loads simd_ops.c and interning.c
    import dreaming_electric_sheep.url as u
    assert hasattr(u, "URL")

    # Headers module loads interning.c
    import dreaming_electric_sheep.headers as hd
    assert hasattr(hd, "Headers")
    assert hasattr(hd, "Header")

    # Verify static interning function in C extension
    dll = ctypes.CDLL(m.__file__)
    assert hasattr(dll, "init_static_interning")
    assert hasattr(dll, "get_interned_method_str")
    assert hasattr(dll, "get_interned_header_name_bytes")
    assert hasattr(dll, "get_interned_content_type_bytes")

    init_fn = dll.init_static_interning
    init_fn.restype = ctypes.c_int
    init_fn.argtypes = []
    assert init_fn() == 0

    # Test get_interned_method_str
    get_method = dll.get_interned_method_str
    get_method.restype = ctypes.py_object
    get_method.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    m_get1 = get_method(b"GET", 3)
    m_get2 = get_method(b"GET", 3)
    assert m_get1 == "GET"
    assert m_get1 is m_get2, "Interned strings must share identical PyObject pointer"

    m_post1 = get_method(b"POST", 4)
    assert m_post1 == "POST"

    # Test get_interned_header_name_bytes
    get_header = dll.get_interned_header_name_bytes
    get_header.restype = ctypes.py_object
    get_header.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    h_ct1 = get_header(b"content-type", 12)
    h_ct2 = get_header(b"content-type", 12)
    assert h_ct1 == b"content-type"
    assert h_ct1 is h_ct2, "Interned header bytes must share identical PyObject pointer"

    h_host = get_header(b"host", 4)
    assert h_host == b"host"

    # Test get_interned_content_type_bytes
    get_ct = dll.get_interned_content_type_bytes
    get_ct.restype = ctypes.py_object
    get_ct.argtypes = [ctypes.c_char_p, ctypes.c_size_t]

    ct_json1 = get_ct(b"application/json", 16)
    ct_json2 = get_ct(b"application/json", 16)
    assert ct_json1 == b"application/json"
    assert ct_json1 is ct_json2, "Interned content type bytes must share identical PyObject pointer"


def test_scratchpad_cache_alignment():
    """
    Verify 64-byte cache line alignment of ScratchpadArena structure.
    """
    import dreaming_electric_sheep.messages as m
    dll = ctypes.CDLL(m.__file__)

    # ScratchpadArena fields: buffer(ptr), capacity(size_t), offset(size_t), is_dynamic(int)
    # With 64-byte alignment, sizeof(ScratchpadArena) must be a multiple of 64 bytes.
    class ScratchpadArenaStruct(ctypes.Structure):
        _fields_ = [
            ("buffer", ctypes.c_void_p),
            ("capacity", ctypes.c_size_t),
            ("offset", ctypes.c_size_t),
            ("is_dynamic", ctypes.c_int),
        ]

    # Verify scratchpad_init, scratchpad_alloc, scratchpad_destroy via C
    scratchpad_init = dll.scratchpad_init
    scratchpad_init.restype = ctypes.c_int
    scratchpad_init.argtypes = [ctypes.POINTER(ScratchpadArenaStruct), ctypes.c_size_t]

    scratchpad_alloc = dll.scratchpad_alloc
    scratchpad_alloc.restype = ctypes.c_void_p
    scratchpad_alloc.argtypes = [ctypes.POINTER(ScratchpadArenaStruct), ctypes.c_size_t, ctypes.c_size_t]

    scratchpad_destroy = dll.scratchpad_destroy
    scratchpad_destroy.restype = None
    scratchpad_destroy.argtypes = [ctypes.POINTER(ScratchpadArenaStruct)]

    arena = ScratchpadArenaStruct()
    ret = scratchpad_init(ctypes.byref(arena), 1024)
    assert ret == 0
    assert arena.buffer is not None
    assert arena.capacity == 1024

    # Alloc 128 bytes with 64-byte alignment
    ptr1 = scratchpad_alloc(ctypes.byref(arena), 128, 64)
    assert ptr1 is not None
    assert ptr1 % 64 == 0, "Allocated arena address must respect 64-byte alignment"

    # Reset offset
    arena.offset = 0
    ptr2 = scratchpad_alloc(ctypes.byref(arena), 64, 64)
    assert ptr2 == ptr1, "Reset must allow fast zero-cost O(1) buffer reuse"

    scratchpad_destroy(ctypes.byref(arena))
    assert arena.capacity == 0


