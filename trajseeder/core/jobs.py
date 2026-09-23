import csv
from pathlib import Path


def get_all_job_ids(project_path: Path) -> list[str]:
    """ Returns a list of every job id, grabbed from manifest """

    manifest_path = project_path / "manifest.csv"

    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        job_ids = [row["job_id"] for row in reader]

    return job_ids


def resolve_job_ids(project_path: Path, job_ids: list[str]) -> list[str]:
    """ Check all job IDs exist, add leading 0s where needed, purge duplicates """

    manifest_path = project_path / "manifest.csv"

    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        manifest_jobs = [row["job_id"] for row in reader]

    resolved_jobs = []
    failed_jobs = []

    for job in job_ids:
        try:
            resolved_job = f"{int(job):06d}"
        except ValueError as e:
            raise RuntimeError(f"Non-int job id provided: '{job}'") from e

        if resolved_job in manifest_jobs:
            resolved_jobs.append(resolved_job)
        else:
            failed_jobs.append(job)

    if failed_jobs:
        raise RuntimeError(
            f"Nonexistant jobs provided: {', '.join(failed_jobs)}. "
            "Check manifest.csv for valid job_ids. Leading 0's are appended for you."
        )

    return list(set(resolved_jobs))


def get_all_jobs_status(project_path: Path) -> None:

    # for each job, check its status, and add to the total
        # check heartbeats also
    # then print the totals

    # INITIALIZED: 4213 
    # RUNNING: 84
    # COMPLETE: 5680
    # FAILED: 23

    raise NotImplementedError("Function is not implemented yet.")


def get_job_status(project_path: Path, job_id: str) -> str:
    """ Return the current status of a job """

    status_path = project_path / "jobs" / job_id / "status.txt"

    with open(status_path, 'r') as f:
        return f.read()


def update_job_status(project_path: Path, job_id: str, status: str) -> None:
    """ Update the status.txt file for a job"""

    status_path = project_path / "jobs" / job_id / "status.txt"

    with open(status_path, "w") as f:
        f.write(status)