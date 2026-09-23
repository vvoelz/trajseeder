from .default_serial import DefaultSerialExecutor
from .default_parallel import DefaultParallelExecutor

EXECUTORS = {
    "default-serial": DefaultSerialExecutor,
    "default-parallel": DefaultParallelExecutor,
}