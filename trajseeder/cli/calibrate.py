import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.calibration import run_calibration

def calibrate(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name, must have been initialized with plan"),
    ],
):
    """ Solvate structures according to user specifications and builds jobs. """

    project_path = Path(project_dir).expanduser().resolve()
    
    run_calibration(
        project_path=project_path
    )
