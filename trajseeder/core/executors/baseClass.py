from abc import ABC, abstractmethod
from pathlib import Path


class Executor(ABC):
    """
    Decides how and where core/run.py's run_one_job() gets called on each of your job_ids.
    Executors only own scheduling/dispatch. 
    An Executor must NEVER
    - interact with protocol logic
    - touch OpenMM objects
    - write to status.txt / job.log directly

    Protocol is resolved inside run_one_job() by grabbing it from user project directory.
    One protocol per project!
    """

    @abstractmethod
    def submit(self, project_path: Path, job_ids: list[int]) -> None:
        raise NotImplementedError