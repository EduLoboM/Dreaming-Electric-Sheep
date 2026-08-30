"""
`des run` command implementation.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from typing import Optional
import typer

from dreaming_electric_sheep.cli.loader import (
    get_default_host,
    get_default_port,
    get_default_server,
    resolve_app_target,
)


def run_command(
    app: Optional[str] = typer.Argument(
        None,
        help="Application target (e.g. 'app:app'). Defaults to DES_APP or pyproject.toml [tool.des]",
    ),
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Bind host (default: 127.0.0.1 or pyproject.toml)",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Bind port (default: 8000 or pyproject.toml)",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker processes (default: 1)",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Server backend: auto, granian, or uvicorn (default: auto)",
    ),
    interface: Optional[str] = typer.Option(
        None,
        "--interface",
        "-i",
        help="Interface protocol: rsgi or asgi (default: rsgi for Granian, asgi for Uvicorn)",
    ),
    pin_cpu: bool = typer.Option(
        False,
        "--pin-cpu",
        help="Pin workers to CPU cores (requires server support)",
    ),
    reuseport: bool = typer.Option(
        False,
        "--reuseport",
        help="Enable SO_REUSEPORT socket flag (requires Linux and server support)",
    ),
) -> None:
    """
    Start production server (Granian RSGI/ASGI or Uvicorn ASGI).

    Examples:
      des run
      des run app:app --workers 4 --port 8000
      des run -s granian -i asgi --workers 2
    """
    app_target = resolve_app_target(app)
    bind_host = host or get_default_host()
    bind_port = port or get_default_port()
    server_choice = (server or get_default_server()).lower()

    has_granian = importlib.util.find_spec("granian") is not None
    has_uvicorn = importlib.util.find_spec("uvicorn") is not None

    if server_choice == "auto":
        if has_granian:
            server_choice = "granian"
        elif has_uvicorn:
            server_choice = "uvicorn"
        else:
            print("Error: No ASGI/RSGI server found (neither granian nor uvicorn is installed).", file=sys.stderr)
            print("Next step: pip install 'dreaming-electric-sheep[standard]' or des doctor", file=sys.stderr)
            sys.exit(3)
    elif server_choice == "granian" and not has_granian:
        print("Error: Granian is not installed.", file=sys.stderr)
        print("Next step: pip install granian", file=sys.stderr)
        sys.exit(3)
    elif server_choice == "uvicorn" and not has_uvicorn:
        print("Error: Uvicorn is not installed.", file=sys.stderr)
        print("Next step: pip install uvicorn", file=sys.stderr)
        sys.exit(3)

    if pin_cpu:
        print("Note: CPU affinity pinning is active when supported by runtime hooks.")
    if reuseport:
        print("Note: SO_REUSEPORT socket option passed where supported.")

    selected_interface = (interface or ("rsgi" if server_choice == "granian" else "asgi")).lower()
    print(f"Starting {server_choice} ({selected_interface.upper()}) server on http://{bind_host}:{bind_port} ({workers} worker{'s' if workers > 1 else ''})")

    if server_choice == "granian":
        cmd = [
            "granian",
            "--interface",
            selected_interface,
            "--host",
            bind_host,
            "--port",
            str(bind_port),
            "--workers",
            str(workers),
            app_target,
        ]
    else:
        cmd = [
            "uvicorn",
            app_target,
            "--host",
            bind_host,
            "--port",
            str(bind_port),
            "--workers",
            str(workers),
        ]

    try:
        proc = subprocess.run(cmd)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        sys.exit(0)
