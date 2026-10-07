import typer
from pathlib import Path
from typing import Annotated


def inspect(
    project_dir: Annotated[
        str,
        typer.Option(help="Project directory name"),
    ] = "trajseeder_project"
):
    
    #TODO: this should error if the user hasn't run calibrate (manifest empty)
    project_path = Path(project_dir).expanduser().resolve()

    """
    number of structures -> check length of conforms folder
    structural extents -> grab from from calibration.json if its there, calculate otherwise (convex hull)
    approximate box-size requirements -> same as above
    
    possible problematic input files -> how to detect this?
        -more than 1 chain
        -https://github.com/openmm/pdbfixer
    """

    raise NotImplementedError("Command not implemented")