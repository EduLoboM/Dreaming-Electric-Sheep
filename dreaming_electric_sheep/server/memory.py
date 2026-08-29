"""
Memory management and high-performance allocator integration (jemalloc, mimalloc)
for Dreaming Electric Sheep.

Mitigates heap fragmentation under high concurrency and optimizes memory
consumption for lean infrastructure / VPS environments.
"""

import os
import resource
import shutil
import sys
from typing import Any, Dict, Optional


RECOMMENDED_JEMALLOC_CONF = (
    "background_thread:true,metadata_thp:auto,dirty_decay_ms:1000,muzzy_decay_ms:1000,abort_conf:false"
)

RECOMMENDED_MIMALLOC_OPTS = {
    "MIMALLOC_PAGE_RESET": "1",
    "MIMALLOC_LARGE_OS_PAGES": "0",
    "MIMALLOC_PURGE_DELAY": "10",
}


def find_library_path(lib_name: str) -> Optional[str]:
    """Finds the absolute path of a shared library on the system."""
    search_dirs = [
        "/usr/lib",
        "/usr/lib64",
        "/usr/lib/x86_64-linux-gnu",
        "/usr/lib/aarch64-linux-gnu",
        "/usr/local/lib",
        "/usr/local/lib64",
        "/lib",
        "/lib64",
    ]

    for d in search_dirs:
        if not os.path.exists(d):
            continue
        try:
            for fname in os.listdir(d):
                if fname.startswith(lib_name) and ".so" in fname:
                    return os.path.join(d, fname)
        except (PermissionError, OSError):
            continue

    # Fallback to ldconfig or which if available
    return None


def is_jemalloc_available() -> bool:
    """Checks if jemalloc shared library is available on the system."""
    if find_library_path("libjemalloc") is not None:
        return True
    return False


def is_mimalloc_available() -> bool:
    """Checks if mimalloc shared library is available on the system."""
    if find_library_path("libmimalloc") is not None:
        return True
    return False


def get_current_allocator() -> str:
    """Detects the currently active memory allocator in the Python process."""
    ld_preload = os.environ.get("LD_PRELOAD", "").lower()
    if "jemalloc" in ld_preload:
        return "jemalloc"
    if "mimalloc" in ld_preload:
        return "mimalloc"

    try:
        with open("/proc/self/maps", "r") as f:
            maps_content = f.read().lower()
            if "jemalloc" in maps_content:
                return "jemalloc"
            if "mimalloc" in maps_content:
                return "mimalloc"
    except (FileNotFoundError, PermissionError, OSError):
        pass

    return "pymalloc"


def get_memory_allocator_info() -> Dict[str, Any]:
    """Returns diagnostics and status about the active and available memory allocators."""
    current = get_current_allocator()
    jemalloc_lib = find_library_path("libjemalloc")
    mimalloc_lib = find_library_path("libmimalloc")

    return {
        "active_allocator": current,
        "jemalloc_available": jemalloc_lib is not None,
        "jemalloc_path": jemalloc_lib,
        "mimalloc_available": mimalloc_lib is not None,
        "mimalloc_path": mimalloc_lib,
        "malloc_conf": os.environ.get("MALLOC_CONF"),
        "is_custom_allocator_active": current in ("jemalloc", "mimalloc"),
    }


def configure_allocator(
    allocator: str = "jemalloc",
    custom_conf: Optional[str] = None,
) -> bool:
    """
    Configures the environment variables for the specified high-performance allocator.
    Returns True if the allocator library was found and configured.
    """
    allocator = allocator.lower().strip()
    if allocator == "jemalloc":
        lib_path = find_library_path("libjemalloc")
        if lib_path:
            os.environ["DREAMING_ELECTRIC_SHEEP_ALLOCATOR"] = "jemalloc"
            os.environ["MALLOC_CONF"] = custom_conf or RECOMMENDED_JEMALLOC_CONF
            return True
        return False

    elif allocator == "mimalloc":
        lib_path = find_library_path("libmimalloc")
        if lib_path:
            os.environ["DREAMING_ELECTRIC_SHEEP_ALLOCATOR"] = "mimalloc"
            for k, v in RECOMMENDED_MIMALLOC_OPTS.items():
                os.environ[k] = v
            return True
        return False

    return False


def get_allocator_env_for_process(
    allocator: str = "jemalloc",
    base_env: Optional[Dict[str, str]] = None,
    custom_conf: Optional[str] = None,
) -> Dict[str, str]:
    """
    Constructs an environment dictionary with LD_PRELOAD and tuning flags
    for launching ASGI server worker processes (e.g. Uvicorn, Granian) with
    jemalloc or mimalloc.
    """
    env = dict(base_env if base_env is not None else os.environ)
    allocator = allocator.lower().strip()

    if allocator == "jemalloc":
        lib_path = find_library_path("libjemalloc")
        if lib_path:
            current_preload = env.get("LD_PRELOAD", "")
            if lib_path not in current_preload:
                env["LD_PRELOAD"] = f"{lib_path}:{current_preload}".rstrip(":")
            env["MALLOC_CONF"] = custom_conf or RECOMMENDED_JEMALLOC_CONF
            env["DREAMING_ELECTRIC_SHEEP_ALLOCATOR"] = "jemalloc"

    elif allocator == "mimalloc":
        lib_path = find_library_path("libmimalloc")
        if lib_path:
            current_preload = env.get("LD_PRELOAD", "")
            if lib_path not in current_preload:
                env["LD_PRELOAD"] = f"{lib_path}:{current_preload}".rstrip(":")
            for k, v in RECOMMENDED_MIMALLOC_OPTS.items():
                env[k] = v
            env["DREAMING_ELECTRIC_SHEEP_ALLOCATOR"] = "mimalloc"

    return env


def get_process_memory_usage() -> Dict[str, float]:
    """
    Returns current process memory consumption in Megabytes (MB).
    """
    rss_mb = 0.0
    vms_mb = 0.0

    try:
        with open("/proc/self/statm", "r") as f:
            parts = f.read().split()
            page_size_kb = resource.getpagesize() / 1024.0
            if len(parts) >= 2:
                vms_mb = (int(parts[0]) * page_size_kb) / 1024.0
                rss_mb = (int(parts[1]) * page_size_kb) / 1024.0
                return {"rss_mb": round(rss_mb, 2), "vms_mb": round(vms_mb, 2)}
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        pass

    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # On Linux, ru_maxrss is in kilobytes
        rss_mb = usage.ru_maxrss / 1024.0
    except Exception:
        pass

    return {"rss_mb": round(rss_mb, 2), "vms_mb": round(vms_mb, 2)}
