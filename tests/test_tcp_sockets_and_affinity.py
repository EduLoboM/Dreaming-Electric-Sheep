import os
import socket
import sys

import pytest

from dreaming_electric_sheep.server.affinity import (
    auto_pin_workers,
    get_available_cpu_count,
    get_cpu_affinity,
    is_affinity_supported,
    pin_current_thread_to_cpu,
    pin_worker_to_cpu,
)
from dreaming_electric_sheep.server.sockets import (
    create_server_socket,
    get_socket_options,
    is_so_reuseport_supported,
    is_tcp_defer_accept_supported,
    is_tcp_quickack_supported,
    tune_accepted_socket,
    tune_server_socket,
)


def test_tune_accepted_socket():
    # Create loopback connected socket pair
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    server_conn, _ = listener.accept()

    try:
        # Apply TCP kernel tuning (TCP_NODELAY, TCP_QUICKACK, TCP_DEFER_ACCEPT)
        res = tune_accepted_socket(server_conn, nodelay=True, quickack=True)
        assert res is True

        opts = get_socket_options(server_conn)
        assert opts["tcp_nodelay"] is True

        if is_tcp_quickack_supported():
            assert opts["tcp_quickack"] is not None

        # Test tuning via raw file descriptor (int)
        res_fd = tune_accepted_socket(client.fileno(), nodelay=True)
        assert res_fd is True

    finally:
        server_conn.close()
        client.close()
        listener.close()


def test_create_and_tune_server_socket():
    s = create_server_socket(
        host="127.0.0.1",
        port=0,
        reuse_port=True,
        reuse_addr=True,
        defer_accept=1,
        nodelay=True,
    )
    try:
        assert isinstance(s, socket.socket)
        port = s.getsockname()[1]
        assert port > 0

        opts = get_socket_options(s)
        assert opts["so_reuseaddr"] is True
        if is_so_reuseport_supported():
            assert opts["so_reuseport"] is True
        if is_tcp_defer_accept_supported():
            assert opts["tcp_defer_accept"] is not None

    finally:
        s.close()


def test_tune_socket_invalid_fd():
    assert tune_accepted_socket(-1) is False
    assert tune_server_socket(-1) is False


def test_cpu_affinity_and_thread_pinning():
    cpu_count = get_available_cpu_count()
    assert cpu_count >= 1

    affinity = get_cpu_affinity()
    assert isinstance(affinity, list)
    assert len(affinity) >= 1

    if is_affinity_supported():
        # Pin to CPU 0
        success = pin_worker_to_cpu(0)
        if success:
            new_affinity = get_cpu_affinity()
            assert 0 in new_affinity

        # Auto pin worker 0 and worker 1
        assert auto_pin_workers(0) is True
        assert auto_pin_workers(1) is True

        # Thread pinning via pthread_setaffinity_np
        thread_success = pin_current_thread_to_cpu(0)
        assert isinstance(thread_success, bool)

        # Restore affinity to all CPUs
        if hasattr(os, "sched_setaffinity"):
            try:
                os.sched_setaffinity(0, set(range(cpu_count)))
            except Exception:
                pass

    with pytest.raises(ValueError):
        pin_worker_to_cpu(-1)

    with pytest.raises(ValueError):
        pin_current_thread_to_cpu(-1)

    with pytest.raises(ValueError):
        auto_pin_workers(-1)
