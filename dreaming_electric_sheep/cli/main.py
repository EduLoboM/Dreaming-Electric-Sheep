"""
Dreaming Electric Sheep CLI (`des`) - Main entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    import rich  # noqa: F401
    import typer
except ImportError:

    def main():
        print(
            "Error: Dreaming Electric Sheep CLI requires standard dependencies. "
            'Run: pip install "dreaming-electric-sheep[standard]"',
            file=sys.stderr,
        )
        sys.exit(1)

    if __name__ == "__main__":
        main()
else:
    from dreaming_electric_sheep import __version__
    from dreaming_electric_sheep.cli.cmd_check import check_command
    from dreaming_electric_sheep.cli.cmd_dev import dev_command
    from dreaming_electric_sheep.cli.cmd_new import new_command
    from dreaming_electric_sheep.cli.cmd_routes import routes_command
    from dreaming_electric_sheep.cli.cmd_run import run_command
    from dreaming_electric_sheep.cli.cmd_why import why_command
    from dreaming_electric_sheep.cli.doctor import doctor_command
    from dreaming_electric_sheep.cli.loader import set_project_dir

    CHEAT_SHEET = f"""Dreaming Electric Sheep CLI (des) v{__version__}

Usage: des [COMMAND] [OPTIONS]

Commands:
  new       Create a new project (minimal | api | full)
  dev       Start development server with auto-reload (Granian RSGI)
  run       Start production server (Granian RSGI default)
  check     Validate routes, binders, and configuration
  routes    Inspect compiled routing table
  why       Explain route matching and handler pipeline
  doctor    Inspect C-core, intern tables, and runtime health

Next: run 'des new demo -t api' to scaffold a new REST API project.
"""

    app = typer.Typer(
        name="des",
        help="High-performance CPython 3.13+ serving stack on Granian RSGI.",
        add_completion=False,
        no_args_is_help=False,
    )

    # Register subcommands
    app.command(name="new", help="Create a new Dreaming Electric Sheep project.")(
        new_command
    )
    app.command(
        name="dev", help="Start development server with auto-reload (Granian RSGI)."
    )(dev_command)
    app.command(name="run", help="Start production server (Granian RSGI default).")(
        run_command
    )
    app.command(name="check", help="Validate routes, binders, and configuration.")(
        check_command
    )
    app.command(name="routes", help="Inspect compiled routing table.")(routes_command)
    app.command(
        name="why", help="Explain route matching, parameter binding, and pipeline."
    )(why_command)
    app.command(
        name="doctor", help="Inspect C-core, intern tables, and runtime health."
    )(doctor_command)

    def version_callback(value: bool):
        if value:
            print(f"des (Dreaming Electric Sheep) v{__version__}")
            raise typer.Exit(0)

    @app.callback(invoke_without_command=True)
    def main_callback(
        ctx: typer.Context,
        directory: Optional[Path] = typer.Option(
            None,
            "-C",
            "--directory",
            help="Run command within specified project directory.",
        ),
        version: Optional[bool] = typer.Option(
            None,
            "-v",
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ):
        if directory is not None:
            set_project_dir(directory)

        if ctx.invoked_subcommand is None:
            # Print cheat sheet and exit 0
            print(CHEAT_SHEET)
            raise typer.Exit(0)

    def main():
        try:
            app()
        except SystemExit as exc:
            sys.exit(exc.code)

    if __name__ == "__main__":
        main()
