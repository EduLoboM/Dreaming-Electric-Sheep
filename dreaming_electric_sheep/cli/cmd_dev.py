"""
`des dev` command implementation.
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
    load_application,
    resolve_app_target,
)


def dev_command(
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
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debugpy on port 5678 for debugger attachment (VSCode / PyCharm)",
    ),
) -> None:
    """
    Start development server with auto-reload.

    Examples:
      des dev
      des dev app:app --port 8000
      des dev --debug
      des dev -s granian -i asgi
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
            print(
                "Error: No ASGI/RSGI server found (neither granian nor uvicorn is installed).",
                file=sys.stderr,
            )
            print(
                "Next step: pip install 'dreaming-electric-sheep[standard]' or des doctor",
                file=sys.stderr,
            )
            sys.exit(3)
    elif server_choice == "granian" and not has_granian:
        print("Error: Granian is not installed.", file=sys.stderr)
        print("Next step: pip install granian", file=sys.stderr)
        sys.exit(3)
    elif server_choice == "uvicorn" and not has_uvicorn:
        print("Error: Uvicorn is not installed.", file=sys.stderr)
        print("Next step: pip install uvicorn", file=sys.stderr)
        sys.exit(3)

    if debug:
        try:
            import debugpy

            debugpy.listen(("0.0.0.0", 5678))
            print("debugpy listening on 0.0.0.0:5678 (ready for debugger attach)")
        except ImportError:
            print(
                "Warning: debugpy is not installed. Run: pip install debugpy",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"Warning: could not start debugpy: {e}", file=sys.stderr)

    # Check for docs routes honestly
    docs_msg = ""
    try:
        loaded_app, _ = load_application(app_target)
        for _, route in getattr(loaded_app.router, "iter_with_methods", lambda: [])():
            pattern = getattr(route, "pattern", b"")
            if pattern in (b"/docs", "/docs"):
                docs_msg = f" (docs: http://{bind_host}:{bind_port}/docs)"
                break
    except Exception:
        pass

    selected_interface = (
        interface or ("rsgi" if server_choice == "granian" else "asgi")
    ).lower()
    print(
        f"dev http://{bind_host}:{bind_port} ({server_choice} {selected_interface.upper()}, reload){docs_msg}"
    )

    if server_choice == "granian":
        cmd = [
            "granian",
            "--interface",
            selected_interface,
            "--host",
            bind_host,
            "--port",
            str(bind_port),
            "--reload",
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
            "--reload",
        ]

    try:
        proc = subprocess.run(cmd)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        sys.exit(0)
