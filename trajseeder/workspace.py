import numpy as np
import mdtraj as md


""" 
workspace.py → tools to interact with a workspace

iExample responsibilities of ProjectWorkspace:

load config
load calibration
get_job(job_id)
status_summary()
retry_failed()
verify_outputs()


"""




class ProjectWorkspace:
    """A class to manage the trajseeder workspace."""

    def __init__(self, path):
        """Initialize the class."""
        pass

    def load_config(self):
        """Load the workspace configuration."""
        pass

    def load_calibration(self):
        """Load the calibration information,"""
        pass

    def get_job(self, job_id):
        """Return the specified job."""
        pass

    def status_summary(self):
        """Return a summary of the status of the project."""
        pass

