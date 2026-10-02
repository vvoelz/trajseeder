import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import get_job_status, update_job_status
from trajseeder.core.log_manager import time_since_last_heartbeat, create_logger


def clean(
    project_dir: Annotated[
        str,
        typer.Option(help="Project directory name"),
    ] = "trajseeder_project"
):
    
    project_path = Path(project_dir).expanduser().resolve()
    jobs_path = project_path / "jobs"

    for job_path in jobs_path.iterdir():

        if (get_job_status(job_path) == "FAILED" 
            or (get_job_status(job_path) == "RUNNING" 
                and time_since_last_heartbeat() > 150)):
            
            print(f"Cleaning up job #{job_path.name}", flush=True)
            topo_path = job_path / "topology.pdb"
            system_path = job_path / "system.xml"
            state_path = job_path / "state.xml"
            Path(topo_path).unlink(missing_ok=True)
            Path(system_path).unlink(missing_ok=True)
            Path(state_path).unlink(missing_ok=True)
            
            logger = create_logger(job_path, job_path.name)
            logger.info(f"Cleaned up failed job!")
            update_job_status(job_path, "PENDING")