from trajseeder.core.run import run_one_job
from .baseClass import Executor
from pathlib import Path


class DefaultParallelExecutor(Executor):

    #TODO: Look into the simulation object issue, make sure no conflict

    def submit(self, project_path: Path, job_ids: list[int]):
        raise NotImplementedError("Local parallel execution is not implemented yet.")