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
"""

def run_preparation_script(modeller: Modeller, forcefield: forcefield) -> Simulation:
	
	# Create a system
	system = forcefield.createSystem(modeller.topology, nonbondedMethod=PME, nonbondedCutoff=1.0*nanometer, constraints=HBonds)

	# Define the integrator
	integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds) 
	
	# Create the Simulation
	simulation = Simulation(modeller.topology, system, integrator)
	simulation.context.setPositions(modeller.positions)
	simulation.context.setVelocitiesToTemperature(300*kelvin)

	# Minimize energy
	simulation.minimizeEnergy()

	# NVT
	simulation.step(10000)

	# NPT
	system.addForce(MonteCarloBarostat(1*bar, 300*kelvin))
	simulation.context.reinitialize(preserveState=True)
	simulation.step(10000)

	return simulation