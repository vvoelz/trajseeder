from trajseeder.core.run import run_one_job
from .baseClass import Executor
from pathlib import Path


class DefaultSerialExecutor(Executor):
    def submit(self, project_path: Path, job_ids: list[str]):
        for job_id in job_ids:
            run_one_job(project_path=project_path, job_id=job_id)
