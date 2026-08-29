import os
import pytest
from dreaming_electric_sheep.server.memory import (
    get_memory_allocator_info,
    get_current_allocator,
    is_jemalloc_available,
    is_mimalloc_available,
    configure_allocator,
    get_allocator_env_for_process,
    get_process_memory_usage,
    RECOMMENDED_JEMALLOC_CONF,
    RECOMMENDED_MIMALLOC_OPTS,
)


def test_get_memory_allocator_info():
    info = get_memory_allocator_info()
    assert isinstance(info, dict)
    assert "active_allocator" in info
    assert "jemalloc_available" in info
    assert "mimalloc_available" in info
    assert "is_custom_allocator_active" in info


def test_get_process_memory_usage():
    mem = get_process_memory_usage()
    assert isinstance(mem, dict)
    assert "rss_mb" in mem
    assert "vms_mb" in mem
    assert mem["rss_mb"] >= 0.0


def test_configure_allocator_env():
    # Test configuring jemalloc custom conf
    custom_conf = "background_thread:true,dirty_decay_ms:500"
    env = get_allocator_env_for_process("jemalloc", custom_conf=custom_conf)

    assert isinstance(env, dict)
    if is_jemalloc_available():
        assert "LD_PRELOAD" in env
        assert "jemalloc" in env["LD_PRELOAD"]
        assert env.get("MALLOC_CONF") == custom_conf
        assert env.get("DREAMING_ELECTRIC_SHEEP_ALLOCATOR") == "jemalloc"


def test_configure_mimalloc_env():
    env = get_allocator_env_for_process("mimalloc")
    assert isinstance(env, dict)
    if is_mimalloc_available():
        assert "LD_PRELOAD" in env
        assert "mimalloc" in env["LD_PRELOAD"]
        assert env.get("MIMALLOC_PAGE_RESET") == RECOMMENDED_MIMALLOC_OPTS["MIMALLOC_PAGE_RESET"]
        assert env.get("DREAMING_ELECTRIC_SHEEP_ALLOCATOR") == "mimalloc"
