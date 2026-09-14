import typer
from trajseeder.core.workspace import ProjectWorkspace


def status(
    project: str = typer.Option(".", help="Project directory")
):
    workspace = ProjectWorkspace(project)

    summary = workspace.status_summary()

    for key, value in summary.items():
        print(f"{key}: {value}")
