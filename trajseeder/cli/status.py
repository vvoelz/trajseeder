import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import log_all_jobs_status

def status(
    project_dir: Annotated[
        str,
        typer.Option(help="Project directory name"),
    ] = "trajseeder_project",
):

    project_path = Path(project_dir).expanduser().resolve()
    log_all_jobs_status(project_path)