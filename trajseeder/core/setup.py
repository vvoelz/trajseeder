import shutil
from pathlib import Path
import csv
import json
import glob


    
def create_workspace(structures, config_file, project_dir):
    """ Create a workspace hierarchy of directories and create essential files for this project."""
    
    structures = __resolve_structures(structures)

    if config_file and not __is_valid_json_path(config_file):
        raise RuntimeError("Invalid config file name or path.")

    project_path, jobs_path, logs_path, conforms_path = __create_project_paths(project_dir)

    __create_manifest(project_path)

    if config_file is None:
        __write_project_config(project_path)
    else:
        shutil.copy(config_file, project_path / "config.json")
        log(f"[setup] Copied user provided project config from {config_file}")
        #TODO: Ensure user provied config file actually has everything we need in it

    for structure in structures:
        shutil.copy(structure, conforms_path)
        log(f"[setup] Copied user provided structure, {structure} to project.")
        # TODO ask Dr. Voelz if there is any point in doing this
        # we can move this functionality to calibration and only copy/save the
        # finished calibrated structures. The only point of doing it here is that
        # we could have different versions of a calibrated_conforms/ file if we
        # wanted to run multiple kinds of jobs on the same set of structures.
        # You'd just have to move calibration.json and update manifest differently
        
    log(f"[setup] Completed file structure assembly.")
    log(f"[setup] Modify {project_dir}/config.json as desired before running calibrate command.")
    #TODO: make sure this prints nice regardless of what you put in as project_dir
    
   
# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def __resolve_structures(args):
    """Ensure we are passed a list of valid pdb files, glob as needed"""

    structures = []
    unmatched = []
    for arg in args:
        matches = glob.glob(arg)
        if matches:
            structures.extend(matches)
        else:
            unmatched.append(arg)
    if unmatched:
        raise RuntimeError(f"No files matched: {', '.join(unmatched)}")
    
    non_pdb = [s for s in structures if not s.lower().endswith(".pdb")]
    if non_pdb:
        raise RuntimeError(f"Non-.pdb files provided: {', '.join(non_pdb)}")
    
    return structures


def __is_valid_json_path(path_str: str) -> bool:
    """Ensure a valid path to an existing JSON file"""

    try:
        path = Path(path_str)
        path.resolve()
        return path.suffix.lower() == '.json'
        
    except (OSError, ValueError):
        return False


def __create_project_paths(project_dir):
    """Build the directories for the project."""

    project_path = Path(project_dir).expanduser().resolve()

    if project_path.exists():
        raise RuntimeError("Project directory already exists")

    project_path.mkdir()
    log(f"[setup] Created project workspace: {project_path}")
    
    jobs_path = project_path / "jobs"
    jobs_path.mkdir()
    log(f"[setup] Created jobs dir in workspace: {jobs_path}")

    logs_path = project_path / "logs"
    logs_path.mkdir()
    log(f"[setup] Created logs dir in workspace: {logs_path}")

    conforms_path = project_path / "conforms"
    conforms_path.mkdir()
    log(f"[setup] Created conforms dir in workspace: {conforms_path}")

    return (project_path, jobs_path, logs_path, conforms_path)


def __write_project_config(project_path):
    """Write the project-level config.json file."""

    config = {
        "config_version": 1,

        "forcefield_files": [
            "amber14-all.xml",
            "amber14/tip3pfb.xml"
        ],

        "padding_nm": 1.2,
        "ionicStrength": 0.0,
        "model":'tip3p',
        "positiveIon":'Na+',
        "negativeIon":'Cl-',
        "neutralize": True,
        "residueTemplates": "Not implemented yet, see calibration __equalize_solvation.", 
        "ionCutoff":  0.5,
        "randomSeed": 12345,

        "nonbonded_method": "PME",
        "nonbonded_cutoff_nm": 1.0,

        "constraints": "HBonds",
        "rigid_water": True,

        "temperature_kelvin": 300.0,
        "pressure_bar": 1.0,

        "timestep_fs": 2.0,

        "integrator_friction_per_ps": 1.0,

        "npt_equilibration_steps": 500000
    }

    config_path = project_path / "config.json"

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    log(f"[setup] Wrote project config: {config_path}")


def __create_manifest(project_path):
    """Create the manifest.csv file."""

    manifest_path = project_path / "manifest.csv"

    with open(manifest_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["job_id", "structure_file"])

    log(f"[setup] Created manifest: {manifest_path}")








