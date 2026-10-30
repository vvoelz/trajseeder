import csv
from pathlib import Path
from trajseeder.core.log_manager import time_since_last_heartbeat, create_logger


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

    return list(dict.fromkeys(resolved_jobs))


def confirm_calibrated(project_path: Path) -> None:
    """ Check and make sure project has been calibrated, error otherwise """

    manifest_path = project_path / "manifest.csv"
    if not manifest_path.is_file():
        raise FileNotFoundError("manifest.csv not found, did you run setup and calibrate yet?")

    with manifest_path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header row
        num_rows = sum(1 for row in reader if any(field.strip() for field in row))

    if num_rows == 0:
        raise ValueError("manifest.csv has no entires, did you run calibrate yet?")

    jobs_path = project_path / "jobs"
    if not jobs_path.is_dir():
        raise FileNotFoundError("jobs/ directory not found, did you run calibrate yet?")

    num_jobs = sum(1 for job in jobs_path.iterdir())

    if num_jobs != num_rows:
        raise ValueError("Number of jobs does not match number of entires in manifest.")


def log_all_jobs_status(project_path: Path) -> None:

    jobs_path = project_path / "jobs"

    pending = 0
    running = 0
    complete = 0
    failed = 0

    for job_path in jobs_path.iterdir():

        status = get_job_status(job_path)
        
        if status == "PENDING":
            pending+=1
        elif status == "RUNNING":
            if time_since_last_heartbeat(job_path) > 150:
                update_job_status(job_path, "FAILED")
                failed+=1
            else:
                running+=1
        elif status == "COMPLETE":
            complete+=1
        elif status == "FAILED":
            failed+=1
        else:
            # If nothing matches, something broke
            failed+=1

    print(f"PENDING: {pending}")
    print(f"RUNNING: {running}")
    print(f"COMPLETE: {complete}")
    print(f"FAILED: {failed}")


def get_job_status(job_path: Path) -> str:
    """ Return the current status of a job """

    status_path = job_path / "status.txt"

    with open(status_path, 'r') as f:
        status = f.read()
    
    if status == "PENDING":
        return status
    elif status == "RUNNING":
        return status  
    elif status == "COMPLETE":
        return status
    elif status == "FAILED":
        return status
    else:
        # Catch malformed writes
        update_job_status(job_path, "FAILED")
        return "FAILED"


def update_job_status(job_path: Path, status: str) -> None:
    """ Update the status.txt file for a job"""
    """
    PENDING
    RUNNING
    COMPLETE
    FAILED
    """
    status_path = job_path / "status.txt"

    with open(status_path, "w") as f:
        f.write(status)


def clean_up_failed(project_path: Path) -> list[str]:
    """ 
    Detect which jobs failed, remove all their output files,
    set to pending, return list of reset jobs
    """
    
    jobs_path = project_path / "jobs"
    job_list = []

    for job_path in jobs_path.iterdir():

        if (get_job_status(job_path) == "FAILED" 
            or (get_job_status(job_path) == "RUNNING" 
                and time_since_last_heartbeat(job_path) > 150)):
            
            print(f"Cleaning up job #{job_path.name}", flush=True)
            topo_path = job_path / "topology.pdb"
            system_path = job_path / "system.xml"
            state_path = job_path / "state.xml"
            Path(topo_path).unlink(missing_ok=True)
            Path(system_path).unlink(missing_ok=True)
            Path(state_path).unlink(missing_ok=True)
            
            logger = create_logger(job_path, job_path.name)
            logger.info(f"Cleaned up failed job!")
            update_job_status(job_path, "PENDING")

            job_list.append(job_path.name) 

    return job_list