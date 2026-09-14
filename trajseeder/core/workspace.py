import json
from pathlib import Path
import csv
from collections import Counter

from trajseeder.core.jobs import SeedJob


#TODO: This class seems like it will be useful for my version but is not yet implemented

""" 
workspace.py → tools to interact with a workspace

Example responsibilities of ProjectWorkspace:

load config
load calibration
get_job(job_id)
status_summary()
retry_failed()
verify_outputs()
"""

class ProjectWorkspace:
    """A class to manage the trajseeder workspace."""


    def __init__(self, path):

        self.project_path = Path(path).resolve()

        if not self.project_path.exists():
            raise RuntimeError(f"Workspace does not exist: {self.project_path}")

        self.jobs_path = self.project_path / "jobs"
        self.logs_path = self.project_path / "logs"

        if not self.jobs_path.exists():
            raise RuntimeError("Invalid workspace: missing jobs directory")


    def load_config(self)  :
        """Loads the project-level simulation configuration."""    

        config_path = self.project_path / "config.json"

        if not config_path.exists():
            raise RuntimeError("Workspace missing config.json")

        with open(config_path) as f:
            return json.load(f)



    def load_calibration(self):
        """Loads the solvent calibration parameters,"""

        calibration_path = self.project_path / "calibration.json"

        if not calibration_path.exists():
            raise RuntimeError("Workspace missing calibration.json")

        with open(calibration_path) as f:
            return json.load(f)



    def get_job(self, job_id):
        """Return the specified job."""

        job_id_str = f"{job_id:06d}"

        shard = job_id // 1000
        shard_str = f"{shard:03d}"

        job_dir = self.jobs_path / shard_str / job_id_str

        if not job_dir.exists():
            raise RuntimeError(f"Job directory not found: {job_dir}")

        return SeedJob(job_id, job_dir, self)




    def status_summary(self):
        """Return a summary of the status of the project."""

        counts = Counter()

        for shard_dir in self.jobs_path.iterdir():

            if not shard_dir.is_dir():
                continue

            for job_dir in shard_dir.iterdir():

                status_file = job_dir / "status.txt"

                if not status_file.exists():
                    counts["unknown"] += 1
                    continue

                with open(status_file) as f:
                    status = f.read().strip()

                counts[status] += 1

        return dict(counts)

