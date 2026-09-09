import typer

from trajseeder.calibration import run_calibration

def calibrate(
    structures: list[str],
    padding_nm: float = typer.Option(
        1.2,
        help="Solvent padding in nanometers",
    ),
    output: str = typer.Option(
        "calibration.json",
        help="Output calibration file",
    ),
    molarConcentration: float = typer.Option(
        0.0,
        help="Molar concentration, mols of ions per liter of solvent (water)",
    ),
    randomSeed: int = typer.Option(
        12345,
        help="Random seed for placing ions to acheive molar concentration",
    ),
):
    
    #Determine solvent calibration parameters from an ensemble of structures.
    
    run_calibration(
        structures=structures,
        padding_nm=padding_nm,
        output=output,
        molarConcentration=molarConcentration,
        randomSeed=randomSeed
    )
