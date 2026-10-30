import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import get_job_status, update_job_status, confirm_calibrated
from trajseeder.core.verify import verify_completion

def verify(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ]
):
    """ Verify outputs are valid simulation seeds. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)

    jobs_path = project_path / "jobs"

    complete = 0

    for job_path in jobs_path.iterdir():

        if get_job_status(job_path) == "COMPLETE":
            complete+=1
            if not verify_completion(job_path):
                update_job_status(job_path, "FAILED")
                print(f"Job#{job_path.name[-6:]} has issues with outputs, see its log for details.", flush=True)
            else:
                print(f"Job#{job_path.name[-6:]} verified!", flush=True)
    
    if complete == 0: print(f"No completed jobs to verify.")