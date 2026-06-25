import json
import random
from pathlib import Path

import mdtraj as md
import numpy as np


def log(msg: str) -> None:
    print(msg, flush=True)


def compute_structure_extent_nm(structure_path: str) -> float:
    """Return largest Cartesian extent of a structure in nm."""

    traj = md.load(structure_path)

    xyz = traj.xyz[0]  # shape: (n_atoms, 3), units nm

    mins = xyz.min(axis=0)
    maxs = xyz.max(axis=0)

    extents = maxs - mins

    return float(np.max(extents))


def run_calibration(
    structures: list[str],
    n_calibration: int = 10,
    padding_nm: float = 1.2,
    output: str = "calibration.json",
    random_seed: int = 12345,
):
    """Run geometry-based solvent box calibration."""

    if len(structures) == 0:
        raise RuntimeError("No structures provided for calibration.")

    structures = sorted([str(Path(s)) for s in structures])

    rng = random.Random(random_seed)

    if n_calibration > len(structures):
        log(
            f"[calibration] Requested {n_calibration} structures, "
            f"but only {len(structures)} were provided."
        )
        n_calibration = len(structures)

    selected = rng.sample(structures, n_calibration)

    log(f"[calibration] Selected {len(selected)} structures.")

    extents = []

    for structure in selected:
        extent_nm = compute_structure_extent_nm(structure)
        extents.append(extent_nm)

        log(f"[calibration] {structure}: extent = {extent_nm:.3f} nm")

    max_extent_nm = max(extents)

    box_length_nm = max_extent_nm + 2.0 * padding_nm

    calibration = {
        "config_version": 1,
        "calibration_type": "geometry_only",

        "box_length_nm": box_length_nm,
        "max_structure_extent_nm": max_extent_nm,
        "padding_nm": padding_nm,

        "n_waters": None,
        "n_ions": None,
        "salt_concentration_molar": 0.15,

        "n_calibration_structures": n_calibration,
        "random_seed": random_seed,
        "selected_structures": selected,
    }

    with open(output, "w") as f:
        json.dump(calibration, f, indent=2)

    log(f"[calibration] Wrote calibration file: {output}")

    return calibration
