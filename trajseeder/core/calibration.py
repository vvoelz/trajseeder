import os
import csv
import json
import math
import pickle
import random
import tempfile

from functools import partial
from multiprocessing import Pool

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



def run_calibration(project_path, workers):
    """
    For a project established with "trajseeder plan", establishes cannonical 
    box size based on user input. Then solvates all structures in the project
    with the name number of waters and ionic concentration based on config.json.
    Saves results of calibration to calibration.json.

    Assumes clean, unbroken PDBs with no solvent, all different conformations of the same protien
    For example, _max_extent() will return incorrect answers with pre-hydrated structures
    Adding hydrogens is also often important.
    """
    
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

    userExtent, structuresCut = analyze_extents(project_path / "conforms")

    log("Equalizing solvation.")

    tmpdir = tempfile.TemporaryDirectory() 
    tmp_modellers, cannonLen, addedHOH, addedPos, addedNeg = equalize_solvation(structuresCut, userExtent, project_path/"config.json", workers, tmpdir)

    log(f"Saving calibrated structures as jobs and writing manifest")
    
    build_jobs_and_manifest(project_path, tmp_modellers, structuresCut, workers)
    tmpdir.cleanup()

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
    # Assumes there are no other atoms, will break with pre-hydrated conformations!
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

    max_height = 25   # bar height cap in rows, purely cosmetic
    CUTOFF = 13.56 # This extent will likely exceed 250k atoms
    RED, RESET = "\033[91m", "\033[0m"

    n = len(data)
    lo, hi = min(data), max(data)

    if lo == hi:
        print(f"All {n} values are {lo}")
        return

    # Square root rule (+5)
    bins = max(math.ceil(math.sqrt(n)) + 5, 10)
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
    height = min(max_count, max_height)
    # any non-empty bin gets at least one block
    bar_heights = [
        max(1, round((c / max_count) * height)) if c > 0 else 0
        for c in counts
    ]

    # a bin is flagged if it contains the cutoff or lies entirely above it,
    # i.e. its upper edge is past the cutoff
    flagged = [lo + (i + 1) * bin_width > CUTOFF for i in range(bins)]

    # bars, drawn top row first
    for row in range(height, 0, -1):
        if row == height:
            y_label = str(max_count).rjust(y_label_width)
        elif row == 1:
            y_label = "0".rjust(y_label_width)
        else:
            y_label = " " * y_label_width

        line = f"{y_label} │"
        for h, flag in zip(bar_heights, flagged):
            if h >= row:
                block = "█".center(col_width)
                line += f"{RED}{block}{RESET}" if flag else block
            else:
                line += " " * col_width
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


def analyze_extents(structures_path: Path) -> tuple[float, list[str]]:
    """
    Input: a path to your project's structures
    Runs an analysis to inform user's choice for cannonical box length
    Returns their selection and the sorted list of structures within that cutoff
    """
    structures = [str(p) for p in (structures_path).glob("*.pdb")]

    config_path = structures_path / ".." / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    padding = config["padding_nm"]

    extents = np.array([_max_extent(structure) for structure in structures])

    order = np.argsort(extents, kind='stable')
    sorted_extents = extents[order]
    sorted_structures = [structures[i] for i in order]
    sorted_extents = sorted_extents + (2*padding)

    _print_histogram(sorted_extents)

    percentiles = list(range(5, 101, 5))
    extents = np.percentile(sorted_extents, percentiles, method='nearest')

    label_w = len("Percentile:")
    col_w = max(len(f"{e:.2f}") for e in extents) + 2   # sized to the longest number

    pct_line = "Percentile:" + "".join(str(p).rjust(col_w) for p in percentiles)
    ext_line = "Extent:".rjust(label_w) + "".join(f"{e:.2f}".rjust(col_w) for e in extents)
    rule = "-" * len(pct_line)

    print(rule)
    print(pct_line)
    print(ext_line)
    print(rule)

    print("Note: The padding selected in config.json is included in displayed extents.")

    if sorted_extents[-1] >= 13.56:
        n_under = np.searchsorted(sorted_extents, 13.56)  # count of values below the cap
        max_pct = (n_under - 1) / (len(sorted_extents) - 1) * 100 if n_under > 0 else 0
        print(f"\033[91mYour largest extents with padding are expected to exceed "
            f"250k atoms. The largest percentile you could select to remain "
            f"under this cap is {max_pct:.1f}.\033[0m")

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

    return userExtent-2*padding, sorted_structures[:cutoffIndex]


def _save_modeller(m, path):
    """ Save a modeller to disk as a temp file """
    with open(path, "wb") as f:
        pickle.dump((m.topology, m.getPositions()), f, protocol=pickle.HIGHEST_PROTOCOL)


def _load_modeller(path):
    """ Load a modeller from a temp file on disk """
    with open(path, "rb") as f:
        topology, pos = pickle.load(f)
    return Modeller(topology, pos)


def _added_HOH_positions(in_path_or_model, prot=frozenset()):
    """ Build a (residue:position) dict of unprotected waters in a model """

    waterPositions = {}
    # Making a (residue:position) dict b/c _addIons() uses it later
    if isinstance(in_path_or_model, (str, os.PathLike)):
        model = _load_modeller(in_path_or_model)
    else:
        model = in_path_or_model

    for r in model.topology.residues():
        if r.name == 'HOH' and (r.chain.id, r.id) not in prot:
            #Uses oxygen's position for the waters
            oxygen = next(atom for atom in r.atoms() if atom.element.symbol == 'O')
            waterPositions[r] = model.positions[oxygen.index]

    return waterPositions


def _solvate_one(in_path: Path, forcefield, model, cannonLen) -> tuple[Path, int]:
    """ Solvates a single modeller with ONLY water. 
        (Loads it from temp file on disk and saves it back when done)"""

    m = _load_modeller(in_path)
    m.addSolvent(forcefield,
                 model=model,
                 boxSize=Vec3(cannonLen, cannonLen, cannonLen) * nanometers,
                 neutralize=False,
                 positiveIon='Na+',
                 negativeIon='Cl-',
                 ionicStrength=0 * molar)

    numAtoms = m.topology.getNumAtoms()
    out_path = in_path.replace(".pkl", "_solvated.pkl")
    _save_modeller(m, out_path)
    os.remove(in_path)          # free disk
    return out_path, numAtoms   # tiny return pack to parent


def _prune_ionize_one(varying, 
                      forcefield,
                      minNumHOH,
                      ionCutoff, 
                      positiveIon, 
                      negativeIon, 
                      ionicStrength, 
                      neutralize, 
                      residueTemplates):
        """ Removes unprotected water molecules in excess of the minimum number waters
            found across all conformations, then randomly converts unportected waters
            to ions to acheive user specified solution."""

        in_path, protHOHs = varying
        model = _load_modeller(in_path)
        addedHOHs = _added_HOH_positions(model, protHOHs)
        surplus = len(addedHOHs) - minNumHOH
        model.delete(random.sample(list(addedHOHs), surplus))
        addedHOHs = _added_HOH_positions(model, protHOHs)

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
        
        out_path = in_path.replace("_solvated.pkl", "_finished.pkl")
        _save_modeller(model, out_path)
        os.remove(in_path)          # free disk
        return out_path             


def equalize_solvation(structures: list[str], userExtent: float, config_path: Path, num_workers: int, tmpdir):
    """
    Inputs:
        structures: a list of strings representing file paths of pdbs
        userExtent: a float holding the edge length of the cubic box to place each structure into in nm
        config_path: a Path for the location of the config file containing solvent parameters
        num_workers: the number of workers to run sections of solvation with
        tmpdir: where we store modeler objects inbetween usages so memory doesn't balloon
    Returns:
        modellers: list[Modeller], one model for each input structure, matching all input parameters and all
            having the same number of water molecules
        cannonLen: float, the cubic box length, 
        minNumHOH: int, number of waters added to each conformation
        addedPos: int, number of positive ions added to each conformation
        addedNeg: int, number of negative ions added to each conformation
    """

    # Load values from user config file
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

    log("Building initial modellers.")

    paths = []
    protected_HOH_sets = []
    has_prot_HOH = None
    num_original_atoms = 0

    def HOH_ids(topology):
        return {(r.chain.id, r.id) for r in topology.residues() if r.name in {'HOH', 'WAT', 'TIP3', 'SOL'}}

    # Build initial models, save them to disk as temp files to prevent OOM
    for i, structure in enumerate(tqdm(structures)):
        pdb = PDBFile(structure)
        modeller = Modeller(pdb.topology, pdb.positions)

        path = os.path.join(tmpdir.name, f"model_{i}.pkl")
        _save_modeller(modeller, path)
        paths.append(path)

        # Checking for existing waters, prevent later overwrites
        if i == 0:
            num_original_atoms = modeller.topology.getNumAtoms()
            first = HOH_ids(modeller.topology)
            has_prot_HOH = bool(first)
            if has_prot_HOH:
                protected_HOH_sets.append(first)
        elif has_prot_HOH:
            protected_HOH_sets.append(HOH_ids(modeller.topology))

        del pdb, modeller  # release before loading the next structure
    
    # Filling this out for later zip length conflict avoidance
    if not has_prot_HOH:
        protected_HOH_sets = [set() for _ in paths]

    # Count initial number of ions in structure
    tempModel = _load_modeller(paths[0])
    posName = positiveIon.rstrip('+-0123456789').upper()
    negName = negativeIon.rstrip('+-0123456789').upper()
    initial_pos_ions = sum(1 for r in tempModel.topology.residues() if r.name == posName)
    initial_neg_ions = sum(1 for r in tempModel.topology.residues() if r.name == negName)

    # Sanity check
    if str(tempModel.topology.getNumChains() + 1) in {c.id for c in tempModel.topology.chains()}:
        raise ValueError("addSolvent() would assign a duplicate chain ID, you have a chain.id = num chains")
    
    del tempModel

    # Initial solvation of each conformation
    log("Performing initial solvation of conformations.")

    solvate = partial(_solvate_one, forcefield=forcefield, model=model, cannonLen=cannonLen)

    if num_workers:
        with Pool(num_workers, maxtasksperchild=1) as pool:
            results = list(tqdm(pool.imap(solvate, paths, chunksize=1), total=len(paths)))
    else:
        results = [solvate(p) for p in tqdm(paths)]
        
    solvated_paths, num_atoms = map(list, zip(*results))

    # The minimum number of added water molecules across all conformations
    minNumHOH = (min(num_atoms) - num_original_atoms)/3
    assert(minNumHOH % 1 == 0)
    minNumHOH = int(minNumHOH)


    # Remove surplus HOHs and add ions to each model
    log("Removing surplus water molecules and ionizing.")

    assert len(solvated_paths) == len(protected_HOH_sets)

    prune_ionize = partial(_prune_ionize_one,
                            forcefield=forcefield,
                            minNumHOH=minNumHOH,
                            ionCutoff=ionCutoff,
                            positiveIon=positiveIon,
                            negativeIon=negativeIon,
                            ionicStrength=ionicStrength,
                            neutralize=neutralize,
                            residueTemplates=residueTemplates)

    jobs = list(zip(solvated_paths, protected_HOH_sets))
    if num_workers:
        with Pool(num_workers, maxtasksperchild=1) as pool:
            finished_paths = list(tqdm(pool.imap(prune_ionize, jobs, chunksize=1), total=len(jobs)))
    else:
        finished_paths = [prune_ionize(job) for job in tqdm(jobs)]

    # Count final number of ions and HOHs in structure
    tempModel = _load_modeller(finished_paths[0])

    final_pos_ions = sum(1 for r in tempModel.topology.residues() if r.name == posName)
    final_neg_ions = sum(1 for r in tempModel.topology.residues() if r.name == negName)

    addedPos = final_pos_ions - initial_pos_ions
    addedNeg = final_neg_ions - initial_neg_ions

    addedHOH = minNumHOH - addedPos - addedNeg
    
    return finished_paths, cannonLen, addedHOH, addedPos, addedNeg


def _save_job(inputs):
    """ Loads a modeller from temp and saves is as PDB for a job. """
    modeller, output_path = inputs

    with open(output_path, "w") as f:
        m = _load_modeller(modeller)
        PDBFile.writeFile(m.getTopology(), m.getPositions(), f)


def build_jobs_and_manifest(project_path, modellers, structuresCut, num_workers: int):
    """Save calibrated structures as jobs and write manifest and log"""

    manifest_path = project_path / "manifest.csv"
    outputs = []
    with open(manifest_path, "a", newline="") as manifest_file:
        writer = csv.writer(manifest_file)

        for i in range(len(modellers)):

            job_path = project_path / "jobs" / f"{i:06d}"
            outputs.append(job_path)
            job_path.mkdir()

            output_path = job_path / "status.txt"
            with open(output_path, "w") as f:
                f.write("PENDING")

            output_path = job_path / "job.log"
            with open(output_path, "w") as f:
                f.write("")

            writer.writerow([f"{i:06d}", f"{structuresCut[i]}"])


    log("Saving job topology and positions.")
    jobs = list(zip(modellers, outputs))

    if num_workers and num_workers > 1:
        with Pool(num_workers, maxtasksperchild=1) as pool:
            list(tqdm(pool.imap(_save_job, jobs, chunksize=1), total=len(jobs)))
    else:
        for job in tqdm(jobs):
            _save_job(job)