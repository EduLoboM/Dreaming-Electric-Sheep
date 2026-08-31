"""
High-Performance TCP Socket Tuning & Kernel Optimization for Dreaming Electric Sheep.

Configures low-latency, high-throughput socket options:
- TCP_NODELAY (disables Nagle's algorithm)
- TCP_QUICKACK (disables delayed ACKs for instant responses on Linux)
- TCP_DEFER_ACCEPT (defers connection acceptance until initial request payload arrives)
- SO_REUSEPORT (enables kernel-level load balancing across multiple worker processes)
"""

import socket
import sys
from typing import Any, Dict, Union

# Constant fallbacks if not present in standard library socket module
TCP_NODELAY = getattr(socket, "TCP_NODELAY", 1)
TCP_QUICKACK = getattr(socket, "TCP_QUICKACK", 12)
TCP_DEFER_ACCEPT = getattr(socket, "TCP_DEFER_ACCEPT", 9)
SO_REUSEPORT = getattr(socket, "SO_REUSEPORT", 15)
SO_REUSEADDR = getattr(socket, "SO_REUSEADDR", 2)
IPPROTO_TCP = getattr(socket, "IPPROTO_TCP", 6)
SOL_SOCKET = getattr(socket, "SOL_SOCKET", 1)


def is_tcp_quickack_supported() -> bool:
    """Checks if TCP_QUICKACK is supported by the OS kernel."""
    return sys.platform.startswith("linux")


def is_tcp_defer_accept_supported() -> bool:
    """Checks if TCP_DEFER_ACCEPT is supported by the OS kernel."""
    return sys.platform.startswith("linux")


def is_so_reuseport_supported() -> bool:
    """Checks if SO_REUSEPORT is supported on the current platform."""
    return (
        hasattr(socket, "SO_REUSEPORT")
        or sys.platform.startswith("linux")
        or sys.platform == "darwin"
    )


def tune_accepted_socket(
    sock: Union[socket.socket, int],
    nodelay: bool = True,
    quickack: bool = True,
    defer_accept: bool = False,
) -> bool:
    """
    Applies TCP kernel optimizations directly after accepting a connection:
    - TCP_NODELAY: Disables packet coalescing / Nagle algorithm for immediate packet delivery.
    - TCP_QUICKACK: Disables delayed ACKs on Linux to send immediate ACKs.
    - TCP_DEFER_ACCEPT: If requested, sets defer accept window.

    Accepts either a socket object or raw file descriptor (int).
    Returns True if tuning succeeded.
    """
    fd = sock.fileno() if isinstance(sock, socket.socket) else sock
    if fd < 0:
        return False

    success = True

    # 1. TCP_NODELAY
    if nodelay:
        try:
            if isinstance(sock, socket.socket):
                sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
            else:
                s = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
                finally:
                    s.detach()
        except (OSError, AttributeError):
            success = False

    # 2. TCP_QUICKACK (Linux)
    if quickack and is_tcp_quickack_supported():
        try:
            if isinstance(sock, socket.socket):
                sock.setsockopt(IPPROTO_TCP, TCP_QUICKACK, 1)
            else:
                s = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.setsockopt(IPPROTO_TCP, TCP_QUICKACK, 1)
                finally:
                    s.detach()
        except (OSError, AttributeError):
            pass

    # 3. TCP_DEFER_ACCEPT (Linux)
    if defer_accept and is_tcp_defer_accept_supported():
        try:
            if isinstance(sock, socket.socket):
                sock.setsockopt(IPPROTO_TCP, TCP_DEFER_ACCEPT, 1)
            else:
                s = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.setsockopt(IPPROTO_TCP, TCP_DEFER_ACCEPT, 1)
                finally:
                    s.detach()
        except (OSError, AttributeError):
            pass

    return success


def tune_server_socket(
    sock: Union[socket.socket, int],
    reuse_port: bool = True,
    reuse_addr: bool = True,
    defer_accept: int = 1,
    nodelay: bool = True,
) -> bool:
    """
    Applies kernel-level socket options to a listening server socket:
    - SO_REUSEPORT: Enables multi-process load balancing across worker instances.
    - SO_REUSEADDR: Allows rapid binding without TIME_WAIT port lock.
    - TCP_DEFER_ACCEPT: Defers wake up until request data is present.
    - TCP_NODELAY: Enables low-latency TCP transmission.
    """
    fd = sock.fileno() if isinstance(sock, socket.socket) else sock
    if fd < 0:
        return False

    target_sock = sock if isinstance(sock, socket.socket) else None
    temp_sock = None
    if target_sock is None:
        try:
            temp_sock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
            target_sock = temp_sock
        except OSError:
            return False

    try:
        # SO_REUSEADDR
        if reuse_addr:
            try:
                target_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            except OSError:
                pass

        # SO_REUSEPORT
        if reuse_port and is_so_reuseport_supported():
            try:
                target_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            except OSError:
                pass

        # TCP_DEFER_ACCEPT (seconds to defer)
        if defer_accept > 0 and is_tcp_defer_accept_supported():
            try:
                target_sock.setsockopt(IPPROTO_TCP, TCP_DEFER_ACCEPT, defer_accept)
            except OSError:
                pass

        # TCP_NODELAY
        if nodelay:
            try:
                target_sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
            except OSError:
                pass

        return True
    finally:
        if temp_sock is not None:
            temp_sock.detach()


def create_server_socket(
    host: str = "127.0.0.1",
    port: int = 8000,
    reuse_port: bool = True,
    reuse_addr: bool = True,
    defer_accept: int = 1,
    nodelay: bool = True,
    backlog: int = 2048,
    family: int = socket.AF_INET,
) -> socket.socket:
    """
    Creates, tunes, binds, and listens on a server socket with optimal kernel options.
    """
    s = socket.socket(family, socket.SOCK_STREAM)
    tune_server_socket(
        s,
        reuse_port=reuse_port,
        reuse_addr=reuse_addr,
        defer_accept=defer_accept,
        nodelay=nodelay,
    )
    s.bind((host, port))
    s.listen(backlog)
    return s


def get_socket_options(sock: socket.socket) -> Dict[str, Any]:
    """
    Returns diagnostics on current socket options.
    """
    options: Dict[str, Any] = {}

    try:
        options["tcp_nodelay"] = bool(sock.getsockopt(IPPROTO_TCP, TCP_NODELAY))
    except OSError:
        options["tcp_nodelay"] = None

    if is_tcp_quickack_supported():
        try:
            options["tcp_quickack"] = bool(sock.getsockopt(IPPROTO_TCP, TCP_QUICKACK))
        except OSError:
            options["tcp_quickack"] = None
    else:
        options["tcp_quickack"] = None

    if is_tcp_defer_accept_supported():
        try:
            options["tcp_defer_accept"] = sock.getsockopt(IPPROTO_TCP, TCP_DEFER_ACCEPT)
        except OSError:
            options["tcp_defer_accept"] = None
    else:
        options["tcp_defer_accept"] = None

    if is_so_reuseport_supported():
        try:
            options["so_reuseport"] = bool(sock.getsockopt(SOL_SOCKET, SO_REUSEPORT))
        except OSError:
            options["so_reuseport"] = None
    else:
        options["so_reuseport"] = None

    try:
        options["so_reuseaddr"] = bool(sock.getsockopt(SOL_SOCKET, SO_REUSEADDR))
    except OSError:
        options["so_reuseaddr"] = None

    return options
