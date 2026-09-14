import numpy as np
import mdtraj as md

#TODO: This class seems like it will be useful but is not yet implemented

class SeedJob(object):
    """A class to represent a seed job."""

    def __init__(self, job_id, workspace):
        """Initialize the class."""
        pass

    def load_config(self):
        """Load the configuration."""
        pass

    def run(self):
        """Run the seed job."""

        raise NotImplementedError


    # old code from plan that may be useful later
    """
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
    """

    """
    def __write_job_config(job_dir, job_id):
    #Write the config.json for this job.

    config = {
        "job_id": job_id,
        "structure_file": "input.pdb",
        "random_seed": 12345 + job_id,
    }

    with open(job_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    """