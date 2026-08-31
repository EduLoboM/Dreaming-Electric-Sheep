"""
`des why` signature command implementation.
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


def _format_binder_list(binders: Any) -> list[str]:
    if not binders:
        return []
    res = []
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
            res.append(f"{b_cls}[{type_name}]({param_name})")
        elif param_name:
            res.append(f"{b_cls}({param_name})")
        elif type_name:
            res.append(f"{b_cls}[{type_name}]")
        else:
            res.append(b_cls)
    return res


def why_command(
    method: str = typer.Argument(..., help="HTTP method (e.g. GET, POST)"),
    path: str = typer.Argument(
        ..., help="Request URL path to resolve (e.g. /items/12, /docs)"
    ),
    app: Optional[str] = typer.Argument(
        None,
        help="Application target (e.g. 'app:app'). Defaults to DES_APP or pyproject.toml [tool.des]",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output resolution pipeline as JSON",
    ),
) -> None:
    """
    Explain route matching, parameter binding, middleware order, and JSON serialization.

    Examples:
      des why GET /items/12
      des why GET /docs
      des why POST /items --json
    """
    app_target = resolve_app_target(app)

    try:
        loaded_app, _ = load_and_start_app(app_target)
    except Exception as exc:
        print(f"Error loading application: {exc}", file=sys.stderr)
        sys.exit(2)

    method_upper = method.upper()
    norm_path = path if path.startswith("/") else f"/{path}"

    # Perform real radix router match
    match = loaded_app.router.get_match_by_method_and_path(method_upper, norm_path)

    # Check if match is fallback or no match
    is_fallback = False
    if match is not None:
        if getattr(match, "route", None) is getattr(
            loaded_app.router, "fallback", None
        ):
            is_fallback = True
        elif getattr(getattr(match, "route", None), "pattern", None) in (b"*", "*"):
            is_fallback = True

    if match is None or is_fallback:
        # Find nearest candidates
        candidates = []
        for m, route in loaded_app.router.iter_with_methods():
            p = getattr(route, "pattern", b"")
            p_str = (
                p.decode("utf8", errors="replace") if isinstance(p, bytes) else str(p)
            )
            if p_str != "*" and (norm_path.startswith(p_str[:4]) or m == method_upper):
                candidates.append(f"{m} {p_str}")

        if json_output:
            output_json(
                {
                    "status": "NO_MATCH",
                    "method": method_upper,
                    "path": norm_path,
                    "nearest_routes": candidates[:5],
                }
            )
        else:
            print(f"No match for {method_upper} {norm_path}", file=sys.stderr)
            if candidates:
                print("\nNearest routes:", file=sys.stderr)
                for cand in candidates[:5]:
                    print(f"  {cand}", file=sys.stderr)
        sys.exit(1)

    # Extract match details
    route = match.route
    pattern = getattr(route, "pattern", b"")
    pattern_str = (
        pattern.decode("utf8", errors="replace")
        if isinstance(pattern, bytes)
        else str(pattern)
    )
    values = match.values or {}

    handler = route.handler
    root_fn = getattr(handler, "root_fn", handler)
    binders = getattr(handler, "binders", getattr(root_fn, "binders", None))
    binder_list = _format_binder_list(binders)

    # Check interned method identity honestly
    is_interned = False
    try:
        from dreaming_electric_sheep.messages import Request

        req_probe = Request(method_upper, b"/")
        is_interned = req_probe.method is method_upper
    except Exception:
        is_interned = False

    # Middleware order
    middlewares = []
    for mw in getattr(loaded_app, "middlewares", []):
        mw_name = getattr(mw, "__qualname__", getattr(mw, "__name__", str(mw)))
        middlewares.append(mw_name)

    # JSON encoder
    encoder = "default"
    if (
        getattr(route, "enc_hook", None) is not None
        or getattr(loaded_app, "enc_hook", None) is not None
    ):
        encoder = "enc_hook"
    elif hasattr(root_fn, "return_type"):
        rt = getattr(root_fn, "return_type")
        if getattr(rt, "__module__", "").startswith("msgspec") or getattr(
            getattr(rt, "__class__", None), "__module__", ""
        ).startswith("msgspec"):
            encoder = "msgspec"

    result = {
        "status": "MATCH",
        "method": method_upper,
        "path": norm_path,
        "matched_pattern": pattern_str,
        "path_params": values,
        "handler": f"{root_fn.__module__}:{root_fn.__qualname__}",
        "binders": binder_list,
        "interned_method": is_interned,
        "middlewares": middlewares,
        "json_encoder": encoder,
    }

    if json_output:
        output_json(result)
        sys.exit(0)

    console = get_console()
    if console and sys.stdout.isatty():
        from rich.panel import Panel
        from rich.table import Table

        table = Table(show_header=False, box=None)
        table.add_column("Key", style="bold cyan", width=20)
        table.add_column("Value")

        table.add_row("Request", f"{method_upper} {norm_path}")
        table.add_row("Matched Pattern", pattern_str)
        table.add_row("Path Params", str(values) if values else "(none)")
        table.add_row("Handler", result["handler"])
        table.add_row("Binders", ", ".join(binder_list) if binder_list else "(none)")
        table.add_row("Interned Method", "Yes (singleton)" if is_interned else "No")
        table.add_row("JSON Encoder", encoder)
        table.add_row(
            "Middlewares", " -> ".join(middlewares) if middlewares else "(none)"
        )

        console.print(
            Panel(table, title=f"Route Match: {method_upper} {norm_path}", expand=False)
        )
    else:
        print(f"Request:          {method_upper} {norm_path}")
        print(f"Matched Pattern:  {pattern_str}")
        print(f"Path Params:      {values if values else '(none)'}")
        print(f"Handler:          {result['handler']}")
        print(
            f"Binders:          {', '.join(binder_list) if binder_list else '(none)'}"
        )
        print(f"Interned Method:  {'Yes (singleton)' if is_interned else 'No'}")
        print(f"JSON Encoder:     {encoder}")
        print(
            f"Middlewares:      {' -> '.join(middlewares) if middlewares else '(none)'}"
        )

    sys.exit(0)
