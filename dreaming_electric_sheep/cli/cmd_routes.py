"""
`des routes` command implementation.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

import typer

from dreaming_electric_sheep.cli.loader import (
    get_console,
    load_and_start_app,
    output_json,
    resolve_app_target,
)


def _format_binders(binders: Any) -> str:
    if not binders:
        return "-"
    formatted = []
    for b in binders:
        b_cls = b.__class__.__name__
        param_name = getattr(b, "param_name", None) or getattr(b, "name", None)
        expected_type = getattr(b, "expected_type", None)
        type_name = (
            getattr(expected_type, "__name__", str(expected_type))
            if expected_type
            else ""
        )

        if param_name and type_name:
            formatted.append(f"{b_cls}[{type_name}]({param_name})")
        elif param_name:
            formatted.append(f"{b_cls}({param_name})")
        elif type_name:
            formatted.append(f"{b_cls}[{type_name}]")
        else:
            formatted.append(b_cls)
    return ", ".join(formatted)


def _format_response(handler: Any) -> str:
    root_fn = getattr(handler, "root_fn", handler)
    rt = getattr(root_fn, "return_type", None)
    if rt is not None:
        return getattr(rt, "__name__", str(rt))
    return "-"


def routes_command(
    app: Optional[str] = typer.Argument(
        None,
        help="Application target (e.g. 'app:app'). Defaults to DES_APP or pyproject.toml [tool.des]",
    ),
    method_filter: Optional[str] = typer.Option(
        None,
        "--method",
        "-m",
        help="Filter routes by HTTP method (e.g. GET, POST)",
    ),
    path_filter: Optional[str] = typer.Option(
        None,
        "--path",
        help="Filter routes by path substring or prefix",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output route table as JSON",
    ),
) -> None:
    """
    Display the compiled routing table after application initialization.

    Examples:
      des routes
      des routes --method GET
      des routes --path /items
      des routes --json
    """
    app_target = resolve_app_target(app)

    try:
        loaded_app, _ = load_and_start_app(app_target)
    except Exception as exc:
        print(f"Error loading application: {exc}", file=sys.stderr)
        sys.exit(2)

    rows: list[dict[str, Any]] = []

    for method, route in loaded_app.router.iter_with_methods():
        pattern = getattr(route, "pattern", b"")
        if isinstance(pattern, bytes):
            path_str = pattern.decode("utf8", errors="replace")
        else:
            path_str = str(pattern)

        # Apply filters
        if method_filter and method.upper() != method_filter.upper():
            continue
        if path_filter and path_filter not in path_str:
            continue

        handler = route.handler
        root_fn = getattr(handler, "root_fn", handler)
        binders = getattr(handler, "binders", getattr(root_fn, "binders", None))
        binders_str = _format_binders(binders)
        response_str = _format_response(handler)
        handler_name = f"{root_fn.__module__}:{root_fn.__qualname__}"

        rows.append(
            {
                "method": method,
                "path": path_str,
                "handler": handler_name,
                "binders": binders_str,
                "response": response_str,
            }
        )

    if json_output:
        output_json(rows)
        sys.exit(0)

    console = get_console()
    if console and sys.stdout.isatty():
        from rich.table import Table

        table = Table(
            title="Compiled Routing Table", show_header=True, header_style="bold cyan"
        )
        table.add_column("Method", style="bold green", width=8)
        table.add_column("Path", style="bold", min_width=20)
        table.add_column("Handler", style="dim")
        table.add_column("Binders")
        table.add_column("Response", style="cyan")

        for row in rows:
            table.add_row(
                row["method"],
                row["path"],
                row["handler"],
                row["binders"],
                row["response"],
            )
        console.print(table)
    else:
        # Plain text table
        fmt = "{:<8} {:<24} {:<40} {:<30} {:<15}"
        print(fmt.format("METHOD", "PATH", "HANDLER", "BINDERS", "RESPONSE"))
        print("-" * 120)
        for row in rows:
            print(
                fmt.format(
                    row["method"],
                    row["path"],
                    row["handler"],
                    row["binders"],
                    row["response"],
                )
            )

    sys.exit(0)
