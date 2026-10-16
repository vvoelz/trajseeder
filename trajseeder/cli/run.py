import typer
from pathlib import Path
from typing import Annotated, Optional
from trajseeder.core.executors import EXECUTORS
from trajseeder.core.jobs import get_all_job_ids, resolve_job_ids, confirm_calibrated


def run(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name, must have been calibrated with calibrate"),
    ],
    job_ids: Annotated[
        Optional[list[str]],
        typer.Argument(help="Job ID(s) to run. Omit if using --all."),
    ] = None,
    all_jobs: Annotated[
        bool,
        typer.Option("--all", help="Run every job in the project."),
    ] = False,
    executor: Annotated[
        str,
        typer.Option(help="default-serial | default-parallel | slurm | (others, eventually...)"),
    ] = "default-serial",
):
    """ Run one or more jobs based on user modified preparation script and chosen method of execution. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)

    if all_jobs and job_ids:
        raise typer.BadParameter("Pass either explicit job IDs or --all, not both.")
    if not all_jobs and not job_ids:
        raise typer.BadParameter("Provide at least one job ID, or pass --all.")
    
    resolved_ids = get_all_job_ids(project_path) if all_jobs else resolve_job_ids(project_path, job_ids)
    
    executor_version = EXECUTORS[executor]
    executor_version().submit(project_path=project_path, job_ids=resolved_ids)