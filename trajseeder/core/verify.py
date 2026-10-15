from openmm.app import *
from openmm import *
from openmm.unit import *
from sys import stdout
from pathlib import Path

from trajseeder.core.jobs import get_job_status
from trajseeder.core.log_manager import create_logger


def verify_completion(job_path: Path):
    """ Verify that the files produced by a *completed* job can be run without issue """

    # Sanity check job is completed
    if not get_job_status(job_path) == "COMPLETE":
        raise ValueError("Incomplete job passed to verify_complete()")

    # TODO !!!!! log to the logger WHY it failed, and return false
    logger = create_logger(job_path, job_id)

    # make sure the files are there (i cant imagine they wouldn't be, but w/e)
        # missing system.xml
        # missing state.xml
        # incomplete job directories
        # failed or unknown job states

    # run the little test code to make sure

    return True

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def _simulation_test():

    # 1. Load the companion topology (required to map names/chains to the system)
    pdb = PDBFile('jobs/000000/topology.pdb')

    # 2. Define or load an integrator (required to advance the simulation)
    integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds)

    # 3. Instantiate the Simulation by passing the XML paths directly
    # This deserializes system.xml and automatically applies the coordinates/velocities from state.xml
    simulation = Simulation(
        topology=pdb.topology,
        system='jobs/000000/system.xml',
        integrator=integrator,
        state='jobs/000000/state.xml'
    )

    # 4. Attach reporters and continue running the simulation
    simulation.reporters.append(DCDReporter('output.dcd', 1000))
    simulation.reporters.append(StateDataReporter(
        stdout, 1000, step=True, potentialEnergy=True, temperature=True
    ))

    print("Resuming simulation from state.xml...")
    simulation.step(1000)
