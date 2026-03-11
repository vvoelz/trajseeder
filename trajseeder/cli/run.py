import typer
from trajseeder.workspace import ProjectWorkspace


def run(
    job_id: int,
    project: str = typer.Option(".", help="Project directory")
):
    workspace = ProjectWorkspace(project)

    job = workspace.get_job(job_id)

    job.run()
