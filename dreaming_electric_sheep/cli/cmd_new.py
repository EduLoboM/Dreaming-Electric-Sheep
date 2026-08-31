"""
`des new` command implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from dreaming_electric_sheep.cli.templates import create_project


def new_command(
    project_name: str = typer.Argument(..., help="Name of the new project directory"),
    template: str = typer.Option(
        "minimal",
        "--template",
        "-t",
        help="Project template: minimal, api, or full (default: minimal)",
    ),
    docs: Optional[str] = typer.Option(
        None,
        "--docs",
        help="OpenAPI UI provider for api template: scalar, swagger, or redoc (default: scalar)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite files in target directory if not empty",
    ),
) -> None:
    """
    Create a new Dreaming Electric Sheep project.

    Examples:
      des new demo -t api
      des new demo -t api --docs swagger
      des new demo -t minimal
    """
    target = Path.cwd() / project_name
    create_project(
        project_name=project_name,
        template=template,
        docs=docs,
        target_dir=target,
        force=force,
    )
    print(f"Created {project_name}")
    print(
        f'\nNext steps:\n  cd {project_name}\n  pip install -e ".[standard]"\n  des dev\n'
    )
