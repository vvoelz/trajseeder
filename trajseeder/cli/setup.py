import typer
from typing import Annotated
from trajseeder.core.setup import create_workspace


def setup(
    structures: Annotated[
        list[str],
        typer.Argument(
            help="PDB files or glob patterns, e.g.: ./structures/*.pdb or a.pdb b.pdb",
        ),
    ],
    config_file: Annotated[
        str | None,         
        typer.Option(help="Provide a configuration JSON file to replace default"),
    ] = None,
    project_dir: Annotated[
        str,
        typer.Option(help="Project directory name"),
    ] = "trajseeder_project",
):
    create_workspace(
        structures=structures,
        config_file=config_file,
        project_dir=project_dir
    )
