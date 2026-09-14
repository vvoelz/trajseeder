import typer
from typing import Annotated
from trajseeder.core.calibration import run_calibration

def calibrate(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name, must have been initialized with plan"),
    ], #TODO: do we want default "trajseeder_project"? makes quicker to run
):
    
    run_calibration(
        project_dir=project_dir
    )
