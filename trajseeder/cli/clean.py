import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import clean_up_failed


def clean(
    project_dir: Annotated[
        str,
        typer.Option(help="Project directory name"),
    ] = "trajseeder_project"
):
    
    #TODO: this should error if the user hasn't run calibrate (manifest empty)
    project_path = Path(project_dir).expanduser().resolve()
    clean_up_failed(project_path)