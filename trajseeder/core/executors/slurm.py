from trajseeder.core.run import run_one_job
from .baseClass import Executor
from pathlib import Path

import shutil
import subprocess
import shlex
import getpass
import sys

class SlurmExecutor(Executor):
    def submit(self, project_path: Path, job_ids: list[str]):

        _check_if_valid_slurm_cluster()

        script_path = project_path / "traj_slurm_array.sh"
        if not script_path.exists():
            make_bash_script()
            log("Bash script written!")

        log("Feel free to edit the generated bash script, especially if the default is breaking on your cluster.")
        log("Please report default script breakage on our github.")
        log("Subsequent runs will not produce a new bash script unless the prior script is deleted.")
        
        submit_slurm(script_path, job_ids)



# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def _query(cmd: list[str]) -> str | None:
    """ Run a SLURM command and return its stdout, or None if it fails
    (command missing, accounting not enabled, nonzero exit, etc.) """

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _check_if_valid_slurm_cluster():
    """ Check if we can actually submit SLURM jobs. """

    if shutil.which("sbatch") is None:
        raise RuntimeError("sbatch not found, are you on a slurm cluster (login node)?")
    if shutil.which("sinfo") is None:
        raise RuntimeError("sbatch is installed but, sinfo is not. Cluster misconfiguration suspected.")
    try:
        result = subprocess.run(
            ["sinfo", "-h"], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            "sinfo timed out after 30s. The SLURM controller may be "
            "down or unreachable.") from e
    except OSError as e:
        raise RuntimeError(f"Could not run sinfo: {e}") from e

    if result.returncode != 0:
        raise RuntimeError(
            f"sinfo failed with exit code {result.returncode}: "
            f"{result.stderr.strip()}")


def _get_account() -> str | None:
    """ Return the current user's default SLURM account. """

    return _query(["sacctmgr", "-n", "-P", "show", "user", getpass.getuser(),
                   "format=DefaultAccount"])


def _get_gpu_partitions() -> set[str]:
    """ Return the names of partitions that contain nodes with GPUs. """

    out = _query(["sinfo", "-h", "-o", "%P %G"])
    found = set()
    for line in (out or "").splitlines():
        name, _, gres = line.partition(" ")
        if "gpu" in gres.lower():
            found.add(name.rstrip("*"))
    return found


def _partition_has_gpus(partition: str) -> bool:
    
    gpu_parts = _get_gpu_partitions()
    return any(p in gpu_parts for p in partition.split(","))


def _resolve_partition(requested: str | None) -> str | None:
    """ Return validated partition(s) either the requested one(s), or the default. """

    partitions = _query(["sinfo", "-h", "-o", "%P"])
    if partitions is None:
        raise RuntimeError("No partitions found on cluster.")
    
    lines = partitions.splitlines()
    valid = {p.rstrip("*") for p in lines}
    default = next((p.rstrip("*") for p in lines if p.endswith("*")), None)
    
    if requested is not None:
        bad = [p for p in requested.split(",") if p not in valid]
        if bad:
            raise ValueError(f"Unknown partition(s) {bad}. Available: {valid}")
        return requested
    if default is not None:
        return default
    
    raise RuntimeError("No partition requested and cluster does not have default partition.")


def make_bash_script(project_path: Path,
                     partition: str | None = None,
                     use_gpu: bool | None = None,
                     gpus_per_job: int | None = 1,
                     cpus_per_task: int = 32,
                     mem: str | None = None) -> Path:
    
    # TODO: 
    # How many gpus do we actually want to use?
    # Is there a good way to automatically set CPU usage?
    
    """ Writes the SLURM array script

    --array is not in the script; pass it to sbatch at submit time.
    Each array task calls run_one_job(traj_project, job_id).

    partition: see _resolve_partition. None = cluster default.
    use_gpu: request GPUs only if the partition has them;
    gpus_per_job: GPUs per task when requested; valid range 1 to the GPUs
        per node (OpenMM uses one GPU per simulation, so 1 is typical).
    cpus_per_task: cores per job; 1 to the cores per node.
    mem: e.g. '4G'. None = cluster default (4092 MB per CPU on yours).
        No --time is set, so the partition default applies.
    """
    log_dir = project_path / "slurm_logs"
    log_dir.mkdir(exist_ok=True)

    partition = _resolve_partition(partition) # TODO: partition can be "thing1,thing2"
    has_gpu = _partition_has_gpus(partition)  # if even one of those has GPU this is true which will break later
    if use_gpu and not has_gpu:
        raise RuntimeError(
            f"GPU requested but partition {partition!r} has none. "
            f"Partitions with GPUs: {sorted(_get_gpu_partitions()) or 'none'}")
    want_gpu = has_gpu if use_gpu is None else use_gpu

    directives = [
        "--job-name=trajseeder",
        "--ntasks=1",
        f"--cpus-per-task={cpus_per_task}",
        f"--output={log_dir}/%x_%A_%a.out",
    ]
    if partition:
        directives.append(f"--partition={partition}")
    if (account := _get_account()):
        directives.append(f"--account={account}")
    if mem:
        directives.append(f"--mem={mem}")
    if want_gpu:
        directives.append(f"--gres=gpu:{gpus_per_job}")

    header = "\n".join(f"#SBATCH {d}" for d in directives)

    script = f"""#!/bin/bash
    {header}

    set -euo pipefail
    export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
    export OPENMM_CPU_THREADS="$SLURM_CPUS_PER_TASK"

    {shlex.quote(sys.executable)} -c '
    import sys
    from pathlib import Path
    from trajseeder.core.run import run_one_job
    run_one_job(Path(sys.argv[1]), f"{{int(sys.argv[2]):06d}}")
    ' {shlex.quote(str(project_path))} "$SLURM_ARRAY_TASK_ID"
    """
    script_path = project_path / "trajseeder_array.sh"
    script_path.write_text(script)
    return script_path


def submit_slurm(script_path: Path, job_ids: list[str]) -> str:
    """ Submit jobs to slurm using pre-built bash script. """

    array_spec = ",".join(str(int(j)) for j in job_ids)
    result = subprocess.run(
        ["sbatch", "--parsable", f"--array={array_spec}", str(script_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"sbatch failed: {result.stderr.strip()}")
    return result.stdout.strip()
