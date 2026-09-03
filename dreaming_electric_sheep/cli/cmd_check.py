"""
`des check` command implementation.
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


def check_command(
    app: Optional[str] = typer.Argument(
        None,
        help="Application target (e.g. 'app:app'). Defaults to DES_APP or pyproject.toml [tool.des]",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output check diagnostics as JSON",
    ),
) -> None:
    """
    Validate application routes, compiled binders, and configuration without serving.

    Examples:
      des check
      des check app:app
      des check --json
    """
    app_target = resolve_app_target(app)

    try:
        loaded_app, target_str = load_and_start_app(app_target)
    except Exception as exc:
        if json_output:
            output_json(
                {
                    "status": "FAIL",
                    "app": app_target,
                    "error": str(exc),
                }
            )
        else:
            print(f"Check failed: {exc}", file=sys.stderr)
            print(
                "Next step: Fix syntax / import error or check router bindings",
                file=sys.stderr,
            )
        sys.exit(2)

    # Inspect routes
    routes_list = list(loaded_app.router.iter_with_methods())
    total_routes = len(routes_list)
    handlers_with_binders = 0
    msgspec_handlers = 0
    openapi_bound = False
    ui_provider_name: str | None = None

    for method, route in routes_list:
        handler = route.handler
        root_fn = getattr(handler, "root_fn", handler)
        binders = getattr(handler, "binders", getattr(root_fn, "binders", None))
        if binders:
            handlers_with_binders += 1

        pattern = getattr(route, "pattern", b"")
        if isinstance(pattern, bytes):
            pattern_str = pattern.decode("utf8", errors="replace")
        else:
            pattern_str = str(pattern)

        if pattern_str in ("/openapi.json", "openapi.json"):
            openapi_bound = True

        # Check for UI providers
        handler_qual = getattr(root_fn, "__qualname__", "")
        if "ScalarUIProvider" in handler_qual or "scalar" in handler_qual.lower():
            ui_provider_name = "ScalarUIProvider"
        elif "SwaggerUIProvider" in handler_qual or "swagger" in handler_qual.lower():
            ui_provider_name = "SwaggerUIProvider"
        elif "ReDocUIProvider" in handler_qual or "redoc" in handler_qual.lower():
            ui_provider_name = "ReDocUIProvider"

        # Check msgspec encoders
        if (
            getattr(route, "enc_hook", None) is not None
            or getattr(loaded_app, "enc_hook", None) is not None
        ):
            msgspec_handlers += 1
        elif hasattr(root_fn, "return_type"):
            rt = getattr(root_fn, "return_type")
            if getattr(rt, "__module__", "").startswith("msgspec") or getattr(
                getattr(rt, "__class__", None), "__module__", ""
            ).startswith("msgspec"):
                msgspec_handlers += 1

    # Check mounts
    mounts_list = []
    mount_reg = getattr(loaded_app, "mount_registry", None) or getattr(
        loaded_app, "_mount_registry", None
    )
    if mount_reg is not None:
        mounts_list = list(getattr(mount_reg, "mounted_apps", []) or getattr(mount_reg, "mounts", []) or [])
    mounts_info = (
        f"{len(mounts_list)} mounted apps (ASGI-only)"
        if mounts_list
        else "0 (Native RSGI / ASGI)"
    )

    # Check freeze stub
    cython_freeze_is_stub = True
    radix_router = getattr(loaded_app.router, "_radix_router", None)
    if radix_router is not None and hasattr(radix_router, "freeze"):
        # We know CythonRadixRouter.freeze() in routing.pyx is 'pass'
        cython_freeze_is_stub = True

    result: dict[str, Any] = {
        "status": "OK",
        "app": target_str,
        "routes_count": total_routes,
        "mounts": mounts_info,
        "handlers_with_compiled_binders": handlers_with_binders,
        "msgspec_encoders_count": msgspec_handlers,
        "openapi_bound": openapi_bound,
        "ui_provider": ui_provider_name
        or ("Bound (/docs)" if openapi_bound else "None"),
        "freeze_implementation": "stub (pass)" if cython_freeze_is_stub else "real",
    }

    if json_output:
        output_json(result)
        sys.exit(0)

    console = get_console()
    if console and sys.stdout.isatty():
        from rich.table import Table

        table = Table(
            title="Application Check", show_header=True, header_style="bold cyan"
        )
        table.add_column("Property", style="bold")
        table.add_column("Value")

        table.add_row("Target", result["app"])
        table.add_row("Routes Count", str(result["routes_count"]))
        table.add_row("Mount Topology", result["mounts"])
        table.add_row(
            "Handlers with Binders", str(result["handlers_with_compiled_binders"])
        )
        table.add_row("msgspec Handlers", str(result["msgspec_encoders_count"]))
        table.add_row("OpenAPI Bound", "Yes" if result["openapi_bound"] else "No")
        table.add_row("UI Provider", result["ui_provider"])
        table.add_row(
            "Freeze Status",
            (
                f"WARN: {result['freeze_implementation']}"
                if cython_freeze_is_stub
                else "Real"
            ),
        )
        console.print(table)
    else:
        print(f"Target:                {result['app']}")
        print(f"Routes Count:          {result['routes_count']}")
        print(f"Mount Topology:        {result['mounts']}")
        print(f"Handlers with Binders: {result['handlers_with_compiled_binders']}")
        print(f"msgspec Handlers:      {result['msgspec_encoders_count']}")
        print(f"OpenAPI Bound:         {'Yes' if result['openapi_bound'] else 'No'}")
        print(f"UI Provider:           {result['ui_provider']}")
        print(
            f"Freeze Status:         {'WARN: stub (pass)' if cython_freeze_is_stub else 'real'}"
        )

    sys.exit(0)
