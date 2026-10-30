import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import log_all_jobs_status, confirm_calibrated, log_all_jobs_verbose

def status(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ],
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Report the status of every individual job in detail."),
    ] = False
):
    """ Report the current status of all jobs in a project. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)

    if not verbose:
        log_all_jobs_status(project_path)
    else:
        log_all_jobs_verbose(project_path)