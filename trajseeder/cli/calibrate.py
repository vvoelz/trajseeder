import typer

from trajseeder.calibration import run_calibration


def calibrate(
    structures: list[str],
    n_calibration: int = typer.Option(
        10,
        help="Number of structures to use for calibration",
    ),
    padding_nm: float = typer.Option(
        1.2,
        help="Solvent padding in nanometers",
    ),
    output: str = typer.Option(
        "calibration.json",
        help="Output calibration file",
    ),
    random_seed: int = typer.Option(
        12345,
        help="Random seed for selecting calibration structures",
    ),
):
    """
    Determine solvent calibration parameters from an ensemble of structures.
    """

    run_calibration(
        structures=structures,
        n_calibration=n_calibration,
        padding_nm=padding_nm,
        output=output,
        random_seed=random_seed,
    )
