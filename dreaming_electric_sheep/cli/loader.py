"""
Target application resolution, configuration loading, and output formatting.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# Standard library TOML parser
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

try:
    from rich.console import Console

    _has_rich = True
except ImportError:
    _has_rich = False
    Console = None  # type: ignore


# Global directory override for -C / --directory
_CURRENT_PROJECT_DIR: Path = Path.cwd()


def set_project_dir(path: Path | str | None) -> None:
    """Sets the active project working directory for target and config resolution."""
    global _CURRENT_PROJECT_DIR
    if path is not None:
        target = Path(path).resolve()
        if not target.is_dir():
            print(f"Error: Directory '{path}' does not exist.", file=sys.stderr)
            sys.exit(1)
        _CURRENT_PROJECT_DIR = target
        # Ensure project directory is first in sys.path
        target_str = str(target)
        if target_str in sys.path:
            sys.path.remove(target_str)
        sys.path.insert(0, target_str)
        try:
            os.chdir(target)
        except Exception:
            pass


def get_project_dir() -> Path:
    """Returns the current resolved project directory."""
    return _CURRENT_PROJECT_DIR


def load_pyproject_config() -> dict[str, Any]:
    """Loads [tool.des] section from pyproject.toml in the active project directory."""
    pyproject_file = get_project_dir() / "pyproject.toml"
    if not pyproject_file.is_file():
        return {}

    if tomllib is None:
        return {}

    try:
        content = pyproject_file.read_bytes()
        data = tomllib.loads(content.decode("utf8", errors="replace"))
        tool_section = data.get("tool", {})
        return tool_section.get("des", {})
    except Exception:
        return {}


def resolve_app_target(cli_app: str | None = None) -> str:
    """
    Resolves the application target with strict precedence:
    CLI arg > env DES_APP > pyproject.toml [tool.des] app > 'app:app'
    """
    if cli_app:
        return cli_app

    env_app = os.environ.get("DES_APP")
    if env_app:
        return env_app.strip()

    config = load_pyproject_config()
    config_app = config.get("app")
    if config_app and isinstance(config_app, str):
        return config_app.strip()

    return "app:app"


def get_default_host() -> str:
    """Resolves default host from [tool.des] host or 127.0.0.1."""
    config = load_pyproject_config()
    return str(config.get("host", "127.0.0.1"))


def get_default_port() -> int:
    """Resolves default port from [tool.des] port or 8000."""
    config = load_pyproject_config()
    port = config.get("port", 8000)
    try:
        return int(port)
    except (ValueError, TypeError):
        return 8000


def get_default_server() -> str:
    """Resolves default server from [tool.des] server or 'auto'."""
    config = load_pyproject_config()
    return str(config.get("server", "auto")).lower()


def load_application(app_target: str | None = None):
    """
    Imports and returns the Application instance from the given or resolved target.
    """
    target_str = resolve_app_target(app_target)
    project_dir = get_project_dir()
    if str(project_dir) not in sys.path:
        sys.path.insert(0, str(project_dir))

    if ":" in target_str:
        module_name, attr_name = target_str.split(":", 1)
    else:
        module_name, attr_name = target_str, "app"

    if module_name in sys.modules:
        mod = sys.modules[module_name]
        mod_file = getattr(mod, "__file__", None)
        try:
            if mod_file is None or not Path(mod_file).resolve().is_relative_to(
                project_dir
            ):
                del sys.modules[module_name]
        except Exception:
            del sys.modules[module_name]

    try:
        if module_name in sys.modules:
            mod = importlib.reload(sys.modules[module_name])
        else:
            mod = importlib.import_module(module_name)
    except Exception as exc:
        raise ImportError(
            f"Could not import module '{module_name}' from '{project_dir}': {exc}"
        ) from exc

    if not hasattr(mod, attr_name):
        # Fallback: check 'application' if attr was 'app'
        if attr_name == "app" and hasattr(mod, "application"):
            attr_name = "application"
        else:
            raise AttributeError(
                f"Module '{module_name}' has no attribute '{attr_name}'."
            )

    app_obj = getattr(mod, attr_name)

    # If it's a factory function, call it
    if callable(app_obj) and not hasattr(app_obj, "router"):
        try:
            app_obj = app_obj()
        except Exception as exc:
            raise RuntimeError(
                f"Failed to instantiate application from factory '{target_str}': {exc}"
            ) from exc

    return app_obj, target_str


def load_and_start_app(app_target: str | None = None):
    """
    Imports application and runs app.start() without binding sockets.
    Returns (app, target_str).
    """
    app, target_str = load_application(app_target)
    if not getattr(app, "started", False):
        try:
            asyncio.run(app.start())
        except Exception as exc:
            raise RuntimeError(
                f"Application startup failed during binder normalization / routing: {exc}"
            ) from exc
    return app, target_str


def get_console() -> Any:
    """Returns a configured Rich console if available, respecting NO_COLOR."""
    if _has_rich:
        no_color = "NO_COLOR" in os.environ
        return Console(no_color=no_color, highlight=False)
    return None


def output_json(data: Any) -> None:
    """Emits clean, formatted JSON with no emojis."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_error(message: str, next_step: str | None = None, exit_code: int = 1) -> None:
    """Prints a clean error message and optional next step, then exits."""
    print(f"Error: {message}", file=sys.stderr)
    if next_step:
        print(f"Next step: {next_step}", file=sys.stderr)
    sys.exit(exit_code)
