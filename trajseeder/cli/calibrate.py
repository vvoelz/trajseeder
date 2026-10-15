import typer
from typing import Annotated
from trajseeder.core.calibration import run_calibration

def calibrate(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name, must have been initialized with plan"),
    ],
):
    """ Solvate structures according to user specifications and builds jobs. """
    
    run_calibration(
        project_dir=project_dir
    )
