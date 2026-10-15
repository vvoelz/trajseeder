import typer
from pathlib import Path
from typing import Annotated


def inspect(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ]
):
    
    """ [Not implemented] Check for problematic input files and warn user. """
    raise NotImplementedError("Inspect is planned for a future release. If you would like to see any features, please raise a github issue.")

    #TODO: this should error if it's not a setup dir
    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)

    """
    number of structures -> check length of conforms folder
    structural extents -> grab from from calibration.json if its there, calculate otherwise (convex hull)
    approximate box-size requirements -> same as above
    
    possible problematic input files -> how to detect this?
        -more than 1 chain
        -https://github.com/openmm/pdbfixer
    """

    