
import typer
from pathlib import Path
from typing import Annotated


def retry_failed(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ] = "trajseeder_project",
    executor: Annotated[
        str,
        typer.Option(help="default-serial | default-parallel | (others, eventually...)"),
    ] = "default-serial",
):
        
    project_path = Path(project_dir).expanduser().resolve()
    # TODO: Call the same stuff clean did, then run on the jobs that were cleaned up
    raise NotImplementedError("retry_failed not implemented yet, sorry!")
