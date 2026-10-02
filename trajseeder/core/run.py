import importlib.util
from openmm import *
from openmm.app import *
from .log_manager import *
from .jobs import get_job_status, update_job_status


def run_one_job(project_path: Path, job_id: str):
    """ 
    Run a single job based on the user's protocol.
    The protocol will be grabbed from the project directory automatically.
    The user is free to modify this protocol as they see fit.
    The various executors all have their own way of calling this function.
    but they all must use it to run jobs.
    """

    job_path = project_path / "jobs" / job_id
    logger = create_logger(job_path, job_id)
    heartbeat = Heartbeat(logger, interval=30)

    try:

        # Catch multiple run issues
        status = get_job_status(job_path)
        if status == "COMPLETE":
            logger.info(f"Job already complete, skipping.")
            return     
        elif status == "RUNNING":
            if time_since_last_heartbeat(job_path) > 300:
                logger.info(f"Previous job run detected as failure (silent crash). Continuing with re-run.")
            else:
                logger.info(f"User attempted to run job that is already running.")
                return
        
        # Start run logging
        update_job_status(job_path, "RUNNING")
        logger.info(f"Starting job #{job_id}")
        heartbeat.start()
        print(f"Starting job #{job_id}", flush=True)
        
        # Run preparation script
        logger.info(f"Running provided preperation script.")
        preparedModeller, simulation = _run_user_script(job_path)
        logger.info(f"Preperation script complete")

        # Save completed topology
        logger.info(f"Saving results to topology.pdb")
        topology_path = job_path / "topology.pdb"
        with open(topology_path, "w") as f:
            PDBFile.writeFile(preparedModeller.topology, preparedModeller.positions, f)

        # Save system from the simulation
        logger.info(f"Saving system to system.xml")
        system_path = job_path / "system.xml"
        with open(system_path, 'w') as f:
            f.write(XmlSerializer.serialize(simulation.system))

        # Save state from the simulation
        logger.info(f"Saving state to state.xml")
        state_path = job_path / "state.xml"
        state = simulation.context.getState(getPositions=True, getVelocities=True)
        with open(state_path, 'w') as f:
            f.write(XmlSerializer.serialize(state))

        # Job succeeded
        update_job_status(job_path, "COMPLETE")
        logger.info(f"Job completed!")
        print(f"Finished job #{job_id}", flush=True)
    
    except Exception as e:

        # Job failed
        update_job_status(job_path, "FAILED")
        logger.exception(f"Job failed: {e}")
        print(f"FAILED job #{job_id}", flush=True)

    finally:
        
        heartbeat.stop()

    # TODO: should jobs report to stdout at all? probably useful for them to do that.
    # Be mindful of "propogate=false" flag
    # just doing print statements for now
    # Add second handler for the logger? 
    # heartbeat is also currently .info


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def _run_user_script(job_path: Path):
    """
    Input: A path to a specific job's dir

    Passes off the job's solvated modeller made in calibration step to the user's
    script (placed in known location in project folder by setup step,
    modified by user)

    Returns: whatever the user's preparation_script returns
    (expected to be the finished simulation object)
    (modeller is passed by refrence so it's modified without
    need for a return)
    """

    pdb_path = job_path / "input.pdb"
    script_path = job_path.parent.parent / "preparation_script.py"
    config_path = job_path.parent.parent / "config.json"

    if not pdb_path.is_file():
        raise FileNotFoundError(f"Input PDB not found: {pdb_path}")
    if not script_path.is_file():
        raise FileNotFoundError(f"Preparation script not found: {script_path}")

    # Loading in the user's preparation script
    spec = importlib.util.spec_from_file_location(
        f"trajseeder_user_prep_script", script_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    run_preparation_script = getattr(module, "run_preparation_script", None)
    if not callable(run_preparation_script):
        raise AttributeError(
            f"{script_path.name} must define a function "
            f"'run_preparation_script(modeller: Modeller, forcefield: forcefield)'"
        )

    # Load the pdb file (solvated in calibrate step)
    pdb = PDBFile(str(pdb_path))

    # Specify the forcefield (from calibration file)
    with open(config_path) as f:
        config = json.load(f)
    forcefield = ForceField(config["forcefield_files"][0], config["forcefield_files"][1])

    # Create a Modeller object
    modeller = Modeller(pdb.topology, pdb.positions)

    # Run preparation script on modeller solvated back in calibrate step
    simulation = run_preparation_script(modeller, forcefield)

    return modeller, simulation
