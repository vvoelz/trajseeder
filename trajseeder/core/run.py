from jobs import get_job_status, update_job_status

def run_one_job(project_path, job_id):
    """ 
    Run a single job based on the user's protocol.
    The protocol will be grabbed from the project directory automatically.
    The user is free to modify this protocol as they see fit.
    The various executors all have their own way of calling this function.
    but they all must use it to run jobs.
    """
    
    # TODO: Job failures are only caught on python exceptions
    # this could be very problematic for parallel and slurm
    # should not be too hard to give this function a "heartbeat"
    # and then have status checker (implemented later) update
    # any jobs that do not have a (recent) heartbeat.

    # TODO: See notes on heartbeat and how to ensure catch

    try:

        if get_job_status(project_path, job_id) == "RUNNING":
            # Prevents the same job from running twice at the same time
            # TODO: should this check heartbeat? maybe previous
            # running died and user has not checked status
            # (check status will reset failed / no heartbeat)
            return

        update_job_status(project_path, job_id, "RUNNING")
        
        # !!!!! Update log
        # !!!!! run the job based on provided script
        # !!!!! Update log
        # !!!!! Save topology.pdb result (multiple log updates?)
        # !!!!! Serialize results (multiple log updates?)
        # !!!!! (save system.xml and state.xml)

        update_job_status(project_path, job_id, "COMPLETE")
    
    except:
        update_job_status(project_path, job_id, "FAILED")
        # !!!!! Update log

    raise NotImplementedError("Function not implemented, oh no!")



def check_heartbeat():
    """ Check that a job is still running """

    raise NotImplementedError("Function is not implemented yet.")