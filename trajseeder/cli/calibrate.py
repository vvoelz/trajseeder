import typer
from pathlib import Path
from typing import Annotated, Optional
from trajseeder.core.calibration import run_calibration

def calibrate(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name, must have been initialized with plan"),
    ],
    parallelize: Annotated[
        Optional[int],
        typer.Option(
            "--parallelize",
            help="Solvate models in parallel. Never have more workers than CPUs. See documentation for memory requirements. Takes an int: <number of workers>",
        ),
    ] = None,
):
    """ Solvate structures according to user specifications and builds jobs. """

    project_path = Path(project_dir).expanduser().resolve()

    if parallelize and parallelize < 2:
        raise RuntimeError("If you want to parallelize you must request 2 or more workers.")
    
    run_calibration(
        project_path=project_path,
        workers = parallelize
    )
