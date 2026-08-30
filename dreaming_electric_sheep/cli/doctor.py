"""
System diagnostics and C-core health verification (`des doctor`).
"""
from __future__ import annotations

import importlib.util
import platform
import sys
from typing import Any
import typer

from dreaming_electric_sheep.cli.loader import get_console, output_json

CYTHON_EXTENSIONS = [
    "_des_core",
    "baseapp",
    "routing",
    "core_errors",
    "url",
    "messages",
    "scribe",
    "headers",
    "exceptions",
    "cookies",
    "contents",
]


def run_doctor() -> dict[str, Any]:
    report: dict[str, Any] = {}

    # 1. CPython Runtime & Architecture
    report["python_version"] = sys.version.split()[0]
    report["python_implementation"] = platform.python_implementation()
    report["platform"] = platform.platform()
    report["architecture"] = platform.machine()
    report["gil_disabled"] = getattr(sys, "_is_gil_enabled", lambda: True)() is False

    # 2. C Core Extension & SIMD
    c_core_loaded = False
    simd_isa = "SCALAR"
    intern_addr = "N/A"
    try:
        from dreaming_electric_sheep import _des_core as core
        if core is not None:
            c_core_loaded = True
            simd_isa = str(core.get_simd_isa_info())
            intern_addr = hex(core.get_intern_table_address())
    except Exception as exc:
        simd_isa = f"Failed to load ({exc})"

    report["c_core_loaded"] = c_core_loaded
    report["simd_isa"] = simd_isa
    report["intern_table_addr"] = intern_addr

    # 3. Cython extensions loaded
    loaded_extensions = {}
    extensions_ok = True
    for ext in CYTHON_EXTENSIONS:
        try:
            mod = __import__(f"dreaming_electric_sheep.{ext}", fromlist=[ext])
            loaded_extensions[ext] = bool(mod)
        except Exception:
            loaded_extensions[ext] = False
            extensions_ok = False
    report["cython_extensions"] = loaded_extensions
    report["cython_extensions_all_loaded"] = extensions_ok

    # 4. Intern Singleton Shared Verification
    intern_singleton_ok = False
    try:
        from dreaming_electric_sheep.messages import Request
        req1 = Request("GET", b"/", [(b"content-type", b"application/json")])
        req2 = Request("GET", b"/items", [(b"content-type", b"text/plain")])
        k1 = req1.headers.values[0][0]
        k2 = req2.headers.values[0][0]
        intern_singleton_ok = (req1.method is req2.method) and (k1 is k2) and (intern_addr != "N/A")
    except Exception:
        intern_singleton_ok = False
    report["intern_singleton_shared"] = intern_singleton_ok

    # 5. Scratchpad compiled vs used
    report["scratchpad_compiled"] = c_core_loaded
    report["scratchpad_used_on_hotpath"] = False

    # 6. Freeze stub vs real
    # CythonRadixRouter.freeze() in routing.pyx is pass
    report["freeze_implemented"] = False
    report["freeze_status"] = "stub (pass)"

    # 7. Packages present
    report["packages"] = {
        "granian": importlib.util.find_spec("granian") is not None,
        "uvicorn": importlib.util.find_spec("uvicorn") is not None,
        "uvloop": importlib.util.find_spec("uvloop") is not None,
        "httptools": importlib.util.find_spec("httptools") is not None,
        "msgspec": importlib.util.find_spec("msgspec") is not None,
        "jinja2": importlib.util.find_spec("jinja2") is not None,
    }

    # Determine status: FAIL if broken install, WARN if advert vs reality or missing server, OK otherwise
    is_broken = not c_core_loaded or not extensions_ok or not intern_singleton_ok
    if is_broken:
        report["status"] = "FAIL"
    elif not report["packages"]["granian"] or not report["freeze_implemented"]:
        report["status"] = "WARN"
    else:
        report["status"] = "OK"

    return report


def doctor_command(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output diagnostics as JSON",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Print suggested commands to resolve warnings and failures without mutating system",
    ),
) -> None:
    """
    Inspect SIMD ISA, C-core extensions, intern tables, and environment health.

    Examples:
      des doctor
      des doctor --json
      des doctor --fix
    """
    data = run_doctor()

    if json_output:
        output_json(data)
        sys.exit(2 if data["status"] == "FAIL" else 0)

    console = get_console()
    use_rich = console is not None and sys.stdout.isatty()

    if use_rich:
        from rich.panel import Panel
        from rich.table import Table

        # Runtime Table
        t_runtime = Table(show_header=False, box=None)
        t_runtime.add_column("Property", style="bold cyan", width=26)
        t_runtime.add_column("Value")
        t_runtime.add_row("Python Version", f"{data['python_version']} ({data['python_implementation']})")
        t_runtime.add_row("Platform / OS", f"{data['platform']} ({data['architecture']})")
        t_runtime.add_row("Free-Threaded (NoGIL)", "Active" if data["gil_disabled"] else "Standard GIL")

        # C Core Table
        t_core = Table(show_header=False, box=None)
        t_core.add_column("Property", style="bold cyan", width=26)
        t_core.add_column("Value")
        t_core.add_row("Shared libdes_core", "LOADED" if data["c_core_loaded"] else "NOT LOADED (FAIL)")
        t_core.add_row("Active SIMD ISA", data["simd_isa"])
        t_core.add_row("Static Intern Table", data["intern_table_addr"])
        t_core.add_row("Intern Singleton Shared", "Shared across modules" if data["intern_singleton_shared"] else "NOT SHARED (FAIL)")
        t_core.add_row("Cython Extensions", f"{sum(data['cython_extensions'].values())}/{len(CYTHON_EXTENSIONS)} loaded")
        t_core.add_row("Router Freeze", f"WARN: {data['freeze_status']}")
        t_core.add_row("Scratchpad Arena", "Compiled (unused on hot path)")

        # Packages Table
        t_pkg = Table(show_header=False, box=None)
        t_pkg.add_column("Package", style="bold cyan", width=26)
        t_pkg.add_column("Status")
        for pkg, installed in data["packages"].items():
            t_pkg.add_row(pkg, "Installed" if installed else "Not installed")

        console.print(Panel(t_runtime, title="Runtime & Platform", expand=False))
        console.print(Panel(t_core, title="C Core & Acceleration", expand=False))
        console.print(Panel(t_pkg, title="Server Runtimes & Dependencies", expand=False))
    else:
        print("RUNTIME & PLATFORM:")
        print(f"  Python Version:          {data['python_version']} ({data['python_implementation']})")
        print(f"  Platform / OS:           {data['platform']} ({data['architecture']})")
        print(f"  Free-Threaded (NoGIL):   {'Active' if data['gil_disabled'] else 'Standard GIL'}")
        print("\nC CORE & ACCELERATION:")
        print(f"  Shared libdes_core:      {'LOADED' if data['c_core_loaded'] else 'NOT LOADED'}")
        print(f"  Active SIMD ISA:         {data['simd_isa']}")
        print(f"  Static Intern Table:     {data['intern_table_addr']}")
        print(f"  Intern Singleton Shared: {'Shared' if data['intern_singleton_shared'] else 'NOT SHARED'}")
        print(f"  Cython Extensions:       {sum(data['cython_extensions'].values())}/{len(CYTHON_EXTENSIONS)} loaded")
        print(f"  Router Freeze:           WARN: {data['freeze_status']}")
        print(f"  Scratchpad Arena:        Compiled (unused on hot path)")
        print("\nSERVER RUNTIMES & PACKAGES:")
        for pkg, installed in data["packages"].items():
            print(f"  {pkg:25}: {'Installed' if installed else 'Not installed'}")

    if fix:
        print("\nSuggested remediation commands:")
        if not data["packages"]["granian"]:
            print("  pip install granian")
        if not data["packages"]["uvloop"] and sys.platform != "win32":
            print("  pip install uvloop")
        if not data["cython_extensions_all_loaded"] or not data["c_core_loaded"]:
            print("  pip install -e . --no-build-isolation")

    if data["status"] == "FAIL":
        print("\nFAIL: Broken install detected. Run suggested commands above.", file=sys.stderr)
        sys.exit(2)
    elif data["status"] == "WARN":
        sys.exit(0)
    else:
        sys.exit(0)
