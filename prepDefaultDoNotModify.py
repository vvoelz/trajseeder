from openmm import *
from openmm.app import *
from openmm.unit import nanometer,kelvin,picosecond,picoseconds, bar

"""
Provided here is a standard openMM protocol.
Please feel free to modify the contents of the 
run_preparation_script(modeller: Modeller, forcefield: forcefield) 
function as you see fit. Note that it does not need to be modified
in any way.

modeller is a solvated conform from the calibrate step.
forcefield is what you designated in your project's calibration.json.

MUST RETURN SIMULATION!
Otherwise the runner will fail trying to serialize your
system and state.

Whatever you have in this function will be run on
each job you call with trajseeder run.

If you would like to have your log updated, a python logger is passed to this
function to be used as you see fit. Examples are provided here, but the assumption
is that you are familiar with python logging.

logger.info(f"Your message here")
logger.error(f"Oh no, an error!")

Additionally, functionality is provided for simulation reporters:

from trajseeder.core.log_manager import LoggerWriter

simulation.reporters.append(StateDataReporter(
    LoggerWriter(logger), 1000, step=True, potentialEnergy=True, temperature=True
))
"""

def run_preparation_script(modeller: Modeller, forcefield: forcefield, logger) -> Simulation:
	
	# Create a system
	logger.info(f"User script: Creating system")
	system = forcefield.createSystem(modeller.topology, nonbondedMethod=PME, nonbondedCutoff=1.0*nanometer, constraints=HBonds)

	# Define the integrator
	logger.info(f"User script: Defining integrator")
	integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds) 
	
	# Create the simulation
	logger.info(f"User script: Creating simulation")
	simulation = Simulation(modeller.topology, system, integrator)
	simulation.context.setPositions(modeller.positions)
	simulation.context.setVelocitiesToTemperature(300*kelvin)

	# Minimize energy
	logger.info(f"User script: Minimizing energy")
	simulation.minimizeEnergy()

	# NVT
	logger.info(f"User script: Running NVT")
	simulation.step(10000)

	# NPT (Note: Will cause slight divergence in each jobs box size)
	logger.info(f"User script: Running NPT")
	system.addForce(MonteCarloBarostat(1*bar, 300*kelvin))
	simulation.context.reinitialize(preserveState=True)
	simulation.step(10000)

	return simulation