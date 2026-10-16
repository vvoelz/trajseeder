from openmm import *
from openmm.app import *
from openmm.unit import kelvin,picosecond,picoseconds
from sys import stdout
from pathlib import Path

from trajseeder.core.jobs import get_job_status
from trajseeder.core.log_manager import create_logger, LoggerWriter


def verify_completion(job_path: Path):
    """ Verify that the files produced by a *completed* job can be run without issue.
        Updates the job's log and returns false if there is an issue.
    """

    # NOTE: There are many, many ways that a simulation seed can fail without any
    # actual error. This function should catch most of them, but I expect to update
    # this often to continue to catch more and more rare edge cases.

    # Sanity check: job is completed
    if not get_job_status(job_path) == "COMPLETE":
        raise ValueError("Incomplete job passed to verify_complete()")

    logger = create_logger(job_path, job_path.name[-6:])

    # Sanity check: files are present
    system_path = job_path / "system.xml"
    if not system_path.is_file():
        logger.error("Job marked as complete, but system.xml is missing.")
        return False
    state_path = job_path / "state.xml"
    if not state_path.is_file():
        logger.error("Job marked as complete, but state.xml is missing.")
        return False
    topology_path = job_path / "topology.pdb"
    if not topology_path.is_file():
        logger.error("Job marked as complete, but topology.pdb is missing.")
        return False

    if not _simulation_test(topology_path, system_path, state_path, logger): return False

    return True

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def _simulation_test(topology_path: Path, system_path: Path, state_path: Path, logger):
    """ Ensure files can be loaded into a simulation and run. """

    try:
        pdb = PDBFile(str(topology_path))

        integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds)

        simulation = Simulation(
            topology=pdb.topology,
            system=str(system_path),
            integrator=integrator,
            state=str(state_path)
        )

        simulation.reporters.append(StateDataReporter(
            LoggerWriter(logger), 1000, step=True, potentialEnergy=True, temperature=True
        ))

        simulation.step(1000)
        return True

    except Exception as e:

        logger.exception(f"Reload of simulation failed: {e}")
        return False
