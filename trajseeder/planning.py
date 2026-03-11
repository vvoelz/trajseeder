import shutil
from pathlib import Path
import csv
import json



"""
Pseudocode for planning:

plan(structures, calibration_file, project_dir):

    load calibration.json
    create project directory
    write project config.json
    assign job IDs
    create manifest.csv
    create job directories
    write job configs

"""

def log(msg: str) -> None:
    print(msg, flush=True)



def create_workspace(structures, calibration_file, project_dir, shard_size=1000):
    """Create a workspace hierarchy of directories for this project."""

    # Create the project paths
    project_path, jobs_path, logs_path = __create_project_paths(project_dir)

    # Copy the calibration JSON file in the project
    shutil.copy(calibration_file, project_path / "calibration.json")

    structures = sorted(structures)

    manifest_rows = []

    for job_id, structure in enumerate(structures):

        job_id_str = f"{job_id:06d}"
        shard = job_id // shard_size
        shard_str = f"{shard:03d}"

        job_dir = jobs_path / shard_str / job_id_str
        job_dir.mkdir(parents=True)

        shutil.copy(structure, job_dir / "input.pdb")

        # Write the config for this job
        __write_job_config(job_dir, job_id)

        with open(job_dir / "status.txt", "w") as f:
            f.write("pending\n")

        manifest_rows.append((job_id_str, Path(structure).name))

    # Write the manifest
    __write_manifest(project_path, manifest_rows)
    

    log(f"[planning] Created {len(structures)} jobs")

    

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def __create_project_paths(project_dir):

    project_path = Path(project_dir)

    if project_path.exists():
        raise RuntimeError("Project directory already exists")

    project_path.mkdir()
    log(f"[planning] Created project workspace: {project}")
    
    jobs_path = project_path / "jobs"
    jobs_path.mkdir()
    log(f"[planning] Created jobs dir in workspace: {jobs_dir}")

    logs_path = project_path / "logs"
    logs_path.mkdir()
    log(f"[planning] Created logs dir in workspace: {logs_dir}")

    return (project_path, jobs_dir, logs_path)


def __write_job_config(job_dir, job_id):
    """Write the config.json for this job."""

    config = {
        "job_id": job_id,
        "structure_file": "input.pdb",
        "random_seed": 12345 + job_id,
    }

    with open(job_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)





def __write_manifest(project_path, rows):
    """Write the manifest.csv file."""

    manifest_path = project_path / "manifest.csv"

    with open(manifest_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["job_id", "structure_file"])

        for row in rows:
            writer.writerow(row)

    log(f"[planning] Wrote manifest: {manifest_path}")


def __create_jobs():
    pass



