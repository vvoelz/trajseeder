import logging
from jobs import get_job_status, update_job_status
from log_manager import *


def run_one_job(project_path, job_id):
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

        if get_job_status(project_path, job_id) == "RUNNING":
            # Prevents the same job from running twice at the same time
            # TODO: should this check heartbeat? maybe previous
            # running died and user has not checked status
            # (check status will reset failed / no heartbeat)
            return
        
        # TODO clear the old log file if one exists?
        # at least print a new thing is starting message

        heartbeat.start()
        update_job_status(project_path, job_id, "RUNNING")
        logger.info(f"Starting job #{job_id}")
        
        
        logger.info(f"Running provided preperation script.")
        # !!!!! run the job based on provided script
        logger.info(f"Preperation script complete")

        logger.info(f"Saving results to topology.pdb")
        # !!!!! Save topology.pdb

        logger.info(f"Serializing results")
        # !!!!! Serialize results (multiple log updates?)
        # !!!!! (save system.xml and state.xml)

        update_job_status(project_path, job_id, "COMPLETE")
        logger.info(f"Job completed!")
    
    except Exception as e:
        update_job_status(project_path, job_id, "FAILED")
        logger.exception(f"Job failed: {e}")

    finally:
        heartbeat.stop()

    raise NotImplementedError("Function not implemented, oh no!")
