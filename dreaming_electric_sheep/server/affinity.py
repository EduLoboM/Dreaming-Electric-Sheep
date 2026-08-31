"""
CPU Affinity & Thread Pinning for Dreaming Electric Sheep Workers.

Binds worker threads / processes to dedicated CPU cores via pthread_setaffinity_np
and sched_setaffinity, preventing kernel thread migration and maximizing L1/L2 cache locality.
"""

import ctypes
import os
import sys
from typing import List, Optional


def is_affinity_supported() -> bool:
    """Checks if CPU affinity configuration is supported on current OS."""
    return hasattr(os, "sched_setaffinity") or sys.platform.startswith("linux")


def get_available_cpu_count() -> int:
    """Returns the total number of usable CPU logical cores."""
    try:
        count = os.cpu_count()
        return count if count is not None and count > 0 else 1
    except Exception:
        return 1


def get_cpu_affinity() -> List[int]:
    """Returns the list of CPU cores the current process is permitted to run on."""
    if hasattr(os, "sched_getaffinity"):
        try:
            return sorted(list(os.sched_getaffinity(0)))
        except (OSError, AttributeError):
            pass
    return list(range(get_available_cpu_count()))


def pin_worker_to_cpu(cpu_id: int) -> bool:
    """
    Binds the current process/worker to a specific CPU core using sched_setaffinity.
    Returns True if successfully pinned.
    """
    if cpu_id < 0:
        raise ValueError(f"Invalid cpu_id: {cpu_id}")

    if hasattr(os, "sched_setaffinity"):
        try:
            os.sched_setaffinity(0, {cpu_id})
            return True
        except (OSError, ValueError):
            return False

    return False


def pin_current_thread_to_cpu(cpu_id: int) -> bool:
    """
    Binds the current POSIX thread to a specific CPU core using pthread_setaffinity_np.
    Falls back to sched_setaffinity if pthread C function is unavailable.
    """
    if cpu_id < 0:
        raise ValueError(f"Invalid cpu_id: {cpu_id}")

    if sys.platform.startswith("linux"):
        try:
            # Try pthread via libc
            libc = ctypes.CDLL(None)
            if hasattr(libc, "pthread_setaffinity_np") and hasattr(
                libc, "pthread_self"
            ):
                # Configure ctypes signatures for 64-bit pthread_t
                libc.pthread_self.restype = ctypes.c_ulong
                libc.pthread_self.argtypes = []
                libc.pthread_setaffinity_np.restype = ctypes.c_int
                libc.pthread_setaffinity_np.argtypes = [
                    ctypes.c_ulong,
                    ctypes.c_size_t,
                    ctypes.c_void_p,
                ]

                # cpu_set_t definition on Linux: unsigned long array of 1024 bits (128 bytes)
                cpu_set_size = 128
                num_ulongs = cpu_set_size // ctypes.sizeof(ctypes.c_ulong)
                mask = (ctypes.c_ulong * num_ulongs)()
                # Set bit for cpu_id
                ulong_bits = ctypes.sizeof(ctypes.c_ulong) * 8
                idx = cpu_id // ulong_bits
                bit = cpu_id % ulong_bits
                if idx < num_ulongs:
                    mask[idx] = 1 << bit

                thread_id = libc.pthread_self()
                ret = libc.pthread_setaffinity_np(
                    thread_id, ctypes.sizeof(mask), ctypes.byref(mask)
                )
                if ret == 0:
                    return True
        except Exception:
            pass

    # Fallback to process affinity
    return pin_worker_to_cpu(cpu_id)


def auto_pin_workers(worker_index: int, total_workers: Optional[int] = None) -> bool:
    """
    Automatically calculates and assigns a dedicated CPU core for the worker.
    Evenly distributes worker processes across available physical/logical cores.
    """
    if worker_index < 0:
        raise ValueError(f"Worker index must be non-negative, got {worker_index}")

    cpu_count = get_available_cpu_count()
    cpu_id = worker_index % cpu_count
    return pin_worker_to_cpu(cpu_id)
