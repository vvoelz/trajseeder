import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import confirm_calibrated, get_job_status
from trajseeder.core.export import export_FAH

def export(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ],
    force: Annotated[
        bool,
        typer.Option("--f", help="Don't warn user if not all jobs are finished."),
    ] = False,
):
    """ Package the finished jobs to be run on F@H. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)

    if not force:
        jobs_path = project_path / "jobs"

        num_fails = sum(get_job_status(j)!="COMPLETE" for j in jobs_path.iterdir())

        if num_fails:
            print(f"\033[31m{num_fails}Jobs are incomplete, would you like to package anyway? [Y/N]\033[0m", flush=True)
            user_input = input().strip().lower()
            if user_input != 'y':
                print(f"Export aborted by user.", flush=True)
                return 
    
    export_FAH(project_path)



    

    