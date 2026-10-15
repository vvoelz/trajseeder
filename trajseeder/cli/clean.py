import typer
from pathlib import Path
from typing import Annotated
from trajseeder.core.jobs import clean_up_failed, confirm_calibrated


def clean(
    project_dir: Annotated[
        str,
        typer.Argument(help="Project directory name"),
    ]
):
    """ Clean up failed jobs so they can be re-run. """

    project_path = Path(project_dir).expanduser().resolve()
    confirm_calibrated(project_path)
    clean_up_failed(project_path)