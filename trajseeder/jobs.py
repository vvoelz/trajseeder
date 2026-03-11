import numpy as np
import mdtraj as md


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
