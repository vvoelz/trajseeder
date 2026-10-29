import sys
import shlex
import shutil
import getpass
import textwrap
import subprocess

from pathlib import Path
from .baseClass import Executor

class SlurmExecutor(Executor):
    def submit(self, project_path: Path, job_ids: list[str]):

        _check_if_valid_slurm_cluster()

        script_path = project_path / "traj_slurm_array.sh"
        if not script_path.exists():
            log("Available partitions are:")
            log(_query(["sinfo", "-h", "-o", "%P"]))
            log("Please input partition(s) to use or hit enter for default.")
            log("Format: partition1,partition2")
            partition = input()
            if partition == "": partition = None
            make_bash_script(project_path, partition)
            log("Bash script written!")

            log("Would you like to halt running and edit default bash script? [Y/N]")
            user_input = input().strip().lower()
            if user_input == 'y':
                log("Run aborted by user!")
                return 
            # TODO: Perhaps a way to create script without pretending a job is going to be run?
            
        log("Feel free to edit the generated bash script, especially if the default is breaking on your cluster.")
        log("Please report default script breakage on our github.")
        log("Subsequent runs will not produce a new bash script unless the prior script is deleted.")
        
        submit_slurm(script_path, job_ids)

        log("Sent the following jobs to SLURM queue:")
        for id in job_ids:
            log(f"Job#{id}")


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
    """ Returns true if ALL the partitions have gpu """
    
    gpu_parts = _get_gpu_partitions()
    requested = {p.strip() for p in partition.split(",") if p.strip()}
    return bool(requested) and requested <= gpu_parts


def _pick_cpus_per_task(partitions: str) -> int:
    """ Pick from 1,2,4,8, or 32 cpus per task based on partitions """

    CPU_CHOICES = (1, 2, 4, 8, 16, 32)

    parts = ",".join(p.strip() for p in partitions.split(",") if p.strip())
    if not parts:
        raise ValueError("No partitions given")

    out = _query(["sinfo", "-N", "-h", "-p", parts, "-o", "%c"])
    if out is None:
        raise RuntimeError(f"Could not query sinfo for partitions: {parts}")

    cpus = [int(line.strip().rstrip("+")) for line in out.splitlines() if line.strip()]
    if not cpus:
        raise RuntimeError(f"No nodes found for partitions: {parts}")

    return max((c for c in CPU_CHOICES if c <= max(cpus)), default=1)


def _resolve_partition(input: str | None) -> str | None:
    """Return validated partition(s): the requested one(s), or the cluster default.
    Format for multiple partitions is partition1,partition2,partition3

    (Removes whitespace & treats empty input as None)
    """
    partitions = _query(["sinfo", "-h", "-o", "%P"])
    if partitions is None:
        raise RuntimeError("No partitions found on cluster.")

    lines = [l.strip() for l in partitions.splitlines() if l.strip()]
    valid = {p.rstrip("*") for p in lines}
    default = next((p.rstrip("*") for p in lines if p.endswith("*")), None)

    names = [p.strip() for p in (input or "").split(",") if p.strip()]

    if names:
        bad = [p for p in names if p not in valid]
        if bad:
            raise ValueError(f"Unknown partition(s) {bad}. Available: {sorted(valid)}")
        return ",".join(names)

    if default is not None:
        return default

    raise RuntimeError("No partition requested and cluster does not have default partition.")


def make_bash_script(project_path: Path, 
                     partition: str | None = None) -> Path:   
    """ Writes the SLURM array script based on sensible defaults
        gleaned from the parition's specifications.
    """

    log_dir = project_path / "slurm_logs"
    log_dir.mkdir(exist_ok=True)

    partition = _resolve_partition(partition)
    has_gpu = _partition_has_gpus(partition)

    directives = [
        "--job-name=trajseeder",
        "--ntasks=1",
        f"--cpus-per-task={_pick_cpus_per_task(partition)}",
        f"--output={log_dir}/%x_%A_%a.out",
        f"--partition={partition}"
    ]
    if (account := _get_account()):
        directives.append(f"--account={account}")
    if has_gpu:
        directives.append(f"--gres=gpu:1")

    header = "\n".join(f"#SBATCH {d}" for d in directives)
    
    template = textwrap.dedent("""\
        #!/bin/bash
        __HEADER__

        set -euo pipefail
        export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
        export OPENMM_CPU_THREADS="$SLURM_CPUS_PER_TASK"

        __PYTHON__ -c '
        import sys
        from pathlib import Path
        from trajseeder.core.run import run_one_job
        run_one_job(Path(sys.argv[1]), f"{int(sys.argv[2]):06d}")
        ' __PROJECT__ "$SLURM_ARRAY_TASK_ID"
        """)

    script = (
        template
        .replace("__HEADER__", header)
        .replace("__PYTHON__", shlex.quote(sys.executable))
        .replace("__PROJECT__", shlex.quote(str(project_path)))
    )

    script_path = project_path / "traj_slurm_array.sh"
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
