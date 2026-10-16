
import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.executors import EXECUTORS
from trajseeder.core.jobs import clean_up_failed, confirm_calibrated

def retry_failed(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ],
    executor: Annotated[
        str,
        typer.Option(help="default-serial | default-parallel | slurm | (others, eventually...)"),
    ] = "default-serial",
):
    """ Re-run all failed jobs using user modified script and specified executor. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)
    job_ids = clean_up_failed(project_path)   
    
    executor_version = EXECUTORS[executor]
    executor_version().submit(project_path=project_path, job_ids=job_ids)
