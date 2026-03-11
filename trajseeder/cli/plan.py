import typer
from trajseeder.planning import create_workspace


def plan(
    structures: list[str],
    calibration: str = typer.Option(..., help="Calibration JSON file"),
    project: str = typer.Option("trajseeder_project", help="Project directory"),
):
    create_workspace(
        structures=structures,
        calibration_file=calibration,
        project_dir=project
    )
