from trajseeder.core.run import run_one_job
from .baseClass import Executor
from pathlib import Path


class SlurmExecutor(Executor):
    def submit(self, project_path: Path, job_ids: list[str]):

        raise NotImplementedError("Slurm isn't done yet, sorry!")

        # grab cluster information to fill in basics
            # what degree of control should we give user?
                # start with none, see if users want some.
        
        for job_id in job_ids:

            make_bash_script()
            # make a batch job for each job and put it where it belongs
                # make sure shit is getting logged and marked as needed? (don't conflict w/ run)
                # what if a script exists?
                    # check job status
            
            # run each of these batch jobs (submit them to queue) (how?)
                # needs to catch if the scheduler denies (eg too many jobs currently running)

            raise NotImplementedError("Slurm isn't done yet, sorry!")
            #run_one_job(project_path=project_path, job_id=job_id)




# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def make_bash_script():

    print("work in progress")
