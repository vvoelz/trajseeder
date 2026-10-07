import typer
from pathlib import Path
from typing import Annotated


def verify(
    project_dir: Annotated[
        str,
        typer.Option(help="Project directory name"),
    ] = "trajseeder_project"
):
    
    #TODO: this should error if the user hasn't run calibrate (manifest empty)
    project_path = Path(project_dir).expanduser().resolve()

    """
    This command is intended to detect issues such as:
    missing system.xml
    missing state.xml
    incomplete job directories
    failed or unknown job states
    """

    # TODO: this seems largely covered by trajseeder status BUT
    # - there are cases in which output files will be created without errors
    #   but not actually be valid files!!!
    # - what else (including in earlier steps) could possibly be malformed?

    raise NotImplementedError("Command not implemented")