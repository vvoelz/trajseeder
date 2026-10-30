import csv
import json
import math
import random
import statistics

from tqdm import tqdm
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist

import openmm.unit
from openmm import *
from openmm.app import *
from openmm.app import Modeller, PDBFile
from openmm.unit import nanometer, nanometers, molar


def run_calibration(project_path):
    """
    For a project established with "trajseeder plan", establishes cannonical 
    box size based on user input. Then solvates all structures in the project
    with the name number of waters and ionic concentration based on config.json.
    Saves results of calibration to calibration.json.
    """
    # TODO we are currently assuming a clean, unbroken PDB with no solvent which is not always the case
    # For example, _max_extent() will return incorrect answers with pre-hydrated structures
    # Adding hydrogens is also often important.
    
    # Warn the user if there is an existing calibration file
    if (project_path / "calibration.json").exists():
        log(f"\033[31mThis will overwrite a previous calibration.json.")
        log(f"If you have existing jobs, or have calibrated previously this will break your entire project!")
        log(f"Would you like to continue? [Y/N]\033[0m")
        user_input = input().strip().lower()
        if user_input != 'y':
            log("Calibration aborted by user.")
            return 

    # Check for essential files, are we actually in a project?
    if not(project_path / "config.json").exists(): 
        raise RuntimeError(f"config.json is missing from {project_path}.")
    if not(project_path / "preparation_script.py").exists(): 
        raise RuntimeError(f"preparation_script.py is missing from {project_path}.")
    if not(project_path / "manifest.csv").exists(): 
        raise RuntimeError(f"manifest.csv is missing from {project_path}.")
    if not(project_path / "conforms").exists(): 
        raise RuntimeError(f"conforms/ is missing from {project_path}.")
    if not(project_path / "jobs").exists(): 
        raise RuntimeError(f"jobs/ is missing from {project_path}.")

    log("Proceeding with calibration...")

    userExtent, structuresCut = _analyze_extents(project_path / "conforms")

    log("Equalizing solvation.")
    
    modellers, cannonLen, addedHOH, addedPos, addedNeg = _equalize_solvation(structuresCut, userExtent, project_path/"config.json")

    log(f"Saving calibrated structures as jobs and writing manifest")
    
    _build_jobs_and_manifest(project_path, modellers, structuresCut)

    # Make a json file with the results of the calibration 
    data = {
    "cannonLen": cannonLen,
    "userExtent": userExtent,
    "numWaters": addedHOH,
    "numPosIons": addedPos,
    "numNegIons": addedNeg,
    }
    with open(project_path / "calibration.json", "w") as f:
        json.dump(data, f)

    log("Calibration complete!")


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def log(msg: str) -> None:
    print(msg, flush=True)


def _max_extent(structure_path: str) -> float:
    """Returns the distance between the furthest two atoms on a PDB"""
    # TODO Assumes there are no other atoms, will break with pre-hydrated conformations
    pdb = PDBFile(structure_path)
    #TODO: pdb.positions.unit is usually in nm, but is it always?
    if(pdb.positions.unit != openmm.unit.nanometer):
        log("[red]PDB is using units other than nanometers. This is going to mess things up but I haven't put a fix in yet.[/red]")
    coords = np.array(pdb.positions.value_in_unit(pdb.positions.unit)) 
    hull = ConvexHull(coords)
    pts = coords[hull.vertices]
    return pdist(pts).max()


def _print_histogram(data) -> None:
    """ Prints a histogram to the console to visualize data 
        Input: numpy array of floats """

    print("\n") # makes formatting nice

    max_height = 20   # bar height cap in rows, purely cosmetic
    max_bins = 50     # capped at 50 bins to avoid degenerate cases (e.g. extreme outliers)
    min_bins = 10     # floor so sparse/small datasets still show useful structure
 
    n = len(data)
    lo, hi = min(data), max(data)
 
    if lo == hi:
        print(f"All {n} values are {lo}")
        return
 
    # Freedman-Diaconis rule
    sorted_data = sorted(data)
    q1 = statistics.quantiles(sorted_data, n=4)[0]
    q3 = statistics.quantiles(sorted_data, n=4)[2]
    iqr = q3 - q1
 
    if iqr > 0:
        bin_width = 2 * iqr / (n ** (1 / 3))
        bins = max(1, math.ceil((hi - lo) / bin_width))
    else:
        # Fallback: Sturges' rule
        bins = max(1, math.ceil(math.log2(n) + 1))
 
    bins = max(min_bins, min(bins, max_bins))  # clamp to [min_bins, max_bins]
    bin_width = (hi - lo) / bins
    counts = [0] * bins
 
    for x in data:
        idx = int((x - lo) / bin_width)
        idx = min(idx, bins - 1)  # clamp max value into last bin
        counts[idx] += 1
 
    max_count = max(counts)
    col_width = max(len(str(max_count)), 3) + 1
    y_label_width = len(str(max_count))
 
    # only use as many rows as the fullest bin needs, up to max_height
    height = min(max_count, max_height) if max_count else 1
    bar_heights = [round((c / max_count) * height) if max_count else 0 for c in counts]
 
    # bars, drawn top row first
    for row in range(height, 0, -1):
        if row == height:
            y_label = str(max_count).rjust(y_label_width)
        elif row == 1:
            y_label = "0".rjust(y_label_width)
        else:
            y_label = " " * y_label_width
 
        line = f"{y_label} │"
        for h in bar_heights:
            line += "█".center(col_width) if h >= row else " " * col_width
        print(line)
 
    # x-axis
    print(" " * y_label_width + " └" + "─" * (col_width * bins))
 
    # bin start labels, rotated vertically (one char per row) so they don't collide
    labels = [f"{lo + i * bin_width:.2f}" for i in range(bins)]
    max_label_len = max(len(l) for l in labels)
    padded = [l.rjust(max_label_len) for l in labels]
 
    for row in range(max_label_len):
        line = " " * (y_label_width + 2)
        for l in padded:
            line += l[row].center(col_width)
        print(line)
 
    print(f"\nconformations={n}  bins={bins}  bin width={bin_width:.2f}")


def _analyze_extents(structures_path: Path) -> tuple[float, list[str]]:
    """
    Input: a path to your project's structures
    Runs an analysis to inform user's choice for cannonical box length
    Returns their selection and the sorted list of structures within that cutoff
    """
    structures = [str(p) for p in (structures_path).glob("*.pdb")]

    extents = np.array([_max_extent(structure) for structure in structures])

    order = np.argsort(extents, kind='stable')
    sorted_extents = extents[order]
    sorted_structures = [structures[i] for i in order]

    _print_histogram(extents)

    for i in range(6):
        pct = np.percentile(sorted_extents, 75 + i*5, method='nearest')
        print(f"{75 + i*5}th percentile extent is: {pct:.2f}")

    print("Please select a percentile 0-100.")
    user_input = 100
    while True:
        try:
            user_input = float(input().strip().lower())
            if (user_input < 0) or (user_input > 100):
                raise ValueError()
            break
        except ValueError:
            print("Invalid input, please select a percentile 0-100.")

    userExtent = np.percentile(sorted_extents, user_input, method='nearest')
    cutoffIndex = np.searchsorted(sorted_extents, userExtent, side='right')

    return userExtent, sorted_structures[:cutoffIndex]


def _equalize_solvation(structures: list[str], userExtent: float, config_path: Path):
    """
    Inputs:
        structures: a list of strings representing file paths of pdbs
        userExtent: a float holding the edge length of the cubic box to place each structure into in nm
        config_path: a Path for the location of the config file containing solvent parameters
    Returns:
        modellers: list[Modeller], one model for each input structure, matching all input parameters and all
            having the same number of water molecules
        cannonLen: float, the cubic box length, 
        minNumHOH: int, number of waters added to each conformation
        addedPos: int, number of positive ions added to each conformation
        addedNeg: int, number of negative ions added to each conformation
    """
    with open(config_path) as f:
        config = json.load(f)

    forcefield = ForceField(config["forcefield_files"][0], config["forcefield_files"][1])
    model = config["model"]
    positiveIon = config["positiveIon"]
    negativeIon = config["negativeIon"]
    ionicStrength = config["ionicStrength"]*molar
    neutralize = config["neutralize"]
    residueTemplates = dict() #TODO: how would this work, won't these go stale when we modify things?
    ionCutoff = config["ionCutoff"]*nanometer

    random.seed(config["randomSeed"])

    cannonLen = userExtent + 2*config["padding_nm"]

    # Build initial models
    modellers = []
    log("Building inital modellers.")
    for structure in tqdm(structures):
        pdb = PDBFile(structure)
        modeller = Modeller(pdb.topology, pdb.positions)
        modellers.append(modeller)
    
    # Count initial number of ions in structure
    posName = positiveIon.rstrip('+-').upper()
    negName = negativeIon.rstrip('+-').upper()
    initial_pos_ions = sum(1 for r in modellers[0].topology.residues() if r.name == posName)
    initial_neg_ions = sum(1 for r in modellers[0].topology.residues() if r.name == negName)

    # Creates set of the pre-existing waters in a model so they are not overwritten later
    log("Establishing pre-existing protected water molecules.")
    def HOH_ids(topology):
        return {(r.chain.id, r.id) for r in topology.residues() if r.name == 'HOH'}
    
    protected_HOH_sets = [HOH_ids(m.topology) for m in tqdm(modellers)]

    # Initial solvation of each conformation
    log("Performing initial solvation of conformations.")
    for m in tqdm(modellers):
        m.addSolvent(forcefield, 
                     model=model, 
                     boxSize=Vec3(cannonLen, cannonLen, cannonLen) * nanometers,
                     neutralize=False,
                     positiveIon='Na+',
                     negativeIon='Cl-',
                     ionicStrength=0*molar)
    
    # TODO: Sanity check for id_collision, if we somehow end up with duplicate (residue.chain.id, residue.id)
    # our check for not overwriting pre-existing water breaks.
    # Do we care about reusing residue ID by itself or only with same chain ID?
    # Maybe this should really be handled in inital PDB cleaning that hasn't been implemented
    # by checking for integer ID names?
    # I don't see *why* we'd ever be passed a PDB with a chain or residue already assigned an
    # integer value as it's ID, but if we are, we now have potential for conflicts in the water
    # we add, since it is automatically assigned id = str(#chains/residues + 1).
    # TODO: If we have say, a Cl- with ID="346" in the PDB and then
    # water 346 gets converted to a Cl- later. However, this won't cause issues within a single
    # run of trajseeder since after this we don't care about ID conflicts
    # TODO: Notably, anything working on the models trajseeder makes, will have to deal
    # with the potential ID conflicts, since we produce models with fewer chains/residues than
    # the highest id numbers on the waters and ions we added. This can be fixed by assigning new
    # IDs to these additions at the end of this function

    # Build a (residue:position) dict of unprotected waters in a model
    log("Tracking added water molecules.")
    def added_HOH_positions(model, prot):
        waterPositions = {}
        for r in model.topology.residues():
            if r.name == 'HOH' and (r.chain.id, r.id) not in prot:
                #Uses oxygen's position for the waters
                oxygen = next(atom for atom in r.atoms() if atom.element.symbol == 'O')
                waterPositions[r] = model.positions[oxygen.index]
        return waterPositions
    
    added_HOH_pos_dicts = [
        added_HOH_positions(m, p) 
        for m, p in tqdm(zip(modellers, protected_HOH_sets), total=len(modellers))
    ]

    # The minimum number of added water molecules across all conformations
    minNumHOH = min(len(pos_dict) for pos_dict in added_HOH_pos_dicts)

    # Remove surplus HOHs and add ions to each model
    log("Removing surplus water molecules and ionizing.")
    for model, addedHOHs, protHOHs in tqdm(zip(modellers, added_HOH_pos_dicts, protected_HOH_sets), 
                                         total=len(modellers)):

        surplus = len(addedHOHs) - minNumHOH
        model.delete(random.sample(list(addedHOHs), surplus))

        addedHOHs = added_HOH_positions(model, protHOHs)
        # Note: Because model.delete() makes a new python object, we have new topologies
        # and new residues, so we have to check this again rather than modifying the old dict
        # if we want, we can remove HOHs and add ions in the same step, which is more efficient (by how much?)
        # but requires moving signifigant portions of the _addIons() helper function here.

        model._addIons(forcefield, minNumHOH, addedHOHs, 
                       ionCutoff=ionCutoff, 
                       positiveIon=positiveIon, 
                       negativeIon=negativeIon, 
                       ionicStrength=ionicStrength, 
                       neutralize=neutralize, 
                       residueTemplates=residueTemplates)
        
    # Count final number of ions in structure
    final_pos_ions = sum(1 for r in modellers[0].topology.residues() if r.name == posName)
    final_neg_ions = sum(1 for r in modellers[0].topology.residues() if r.name == negName)

    addedPos = final_pos_ions - initial_pos_ions
    addedNeg = final_neg_ions - initial_neg_ions

    addedHOH = minNumHOH - addedPos - addedNeg
    
    return modellers, cannonLen, addedHOH, addedPos, addedNeg


def _build_jobs_and_manifest(project_path, modellers, structuresCut):
    """Save calibrated structures as jobs and write manifest and log"""

    manifest_path = project_path / "manifest.csv"
    with open(manifest_path, "a", newline="") as manifest_file:
        writer = csv.writer(manifest_file)

        for i, modeller in enumerate(modellers):

            job_path = project_path / "jobs" / f"{i:06d}"
            job_path.mkdir()

            output_path = job_path / "input.pdb"
            with open(output_path, "w") as f:
                PDBFile.writeFile(modeller.getTopology(), modeller.getPositions(), f)

            output_path = job_path / "status.txt"
            with open(output_path, "w") as f:
                f.write("PENDING")

            output_path = job_path / "job.log"
            with open(output_path, "w") as f:
                f.write("")

            writer.writerow([f"{i:06d}", f"{structuresCut[i]}"])