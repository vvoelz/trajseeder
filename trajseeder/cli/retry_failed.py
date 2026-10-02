
import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.executors import EXECUTORS
from trajseeder.core.jobs import clean_up_failed

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
    #TODO: this should error if the user hasn't run calibrate (manifest empty)  

    project_path = Path(project_dir).expanduser().resolve()
    job_ids = clean_up_failed(project_path)   
    
    executor_version = EXECUTORS[executor]
    executor_version().submit(project_path=project_path, job_ids=job_ids)
