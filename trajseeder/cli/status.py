import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import log_all_jobs_status, confirm_calibrated

def status(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ]
):
    """ Report the current status of all jobs in a project. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)
    log_all_jobs_status(project_path)