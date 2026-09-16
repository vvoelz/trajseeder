import typer
from typing import Annotated
from trajseeder.core.run import run_job

#TODO: Needs to be able to handle multiple jobs and running on a cluster.

def run(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name, must have been calibrated with calibrate"),
    ], #TODO: do we want default "trajseeder_project"? makes quicker to run but could cause accidents
    job_id: Annotated[
        int,
        typer.Argument(help="Job ID to be run"),
    ],
):
    
    run_job(
        project_dir=project_dir,
        job_id=job_id
    )