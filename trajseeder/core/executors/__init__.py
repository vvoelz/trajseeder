from .default_serial import DefaultSerialExecutor
from .default_parallel import DefaultParallelExecutor
from .slurm import SlurmExecutor

EXECUTORS = {
    "default-serial": DefaultSerialExecutor,
    "default-parallel": DefaultParallelExecutor,
    "slurm": SlurmExecutor,
}