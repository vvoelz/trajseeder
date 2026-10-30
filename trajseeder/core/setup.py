import csv
import json
import glob
import shutil
from pathlib import Path

   
def create_workspace(structures, config_file, project_dir):
    """ Create a workspace hierarchy of directories and create essential files for this project."""
    
    structures = _resolve_structures(structures)

    if config_file:
        config_path = Path(config_file).expanduser().resolve()
        _validate_config(config_path)

    project_path, jobs_path, conforms_path = _create_project_paths(project_dir)

    _create_manifest(project_path)
    _create_prep_script(project_path)

    if config_file is None:
        _write_project_config(project_path)
    else:
        shutil.copy(config_path, project_path / "config.json")
        log(f"Copied user provided project config from {config_file}")

    for structure in structures:
        shutil.copy(structure, conforms_path)
        log(f"Copied user provided structure, {structure} to project.")
        
    log(f"Completed file structure assembly.")
    log(f"\033[4;32mModify {project_dir}/config.json as desired before running calibrate command.\033[0m")
    log(f"\033[4;32mModify {project_dir}/preparation_script.py as desired before running run command.\033[0m")
   
# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def _resolve_structures(args):
    """Ensure we are passed a list of pdb files, glob as needed"""

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


def _validate_config(config_path: Path):
    """Validate user provided config"""
    #TODO: validate that the values contained within user's json are acceptable

    if config_path.suffix.lower() != ".json":
        raise RuntimeError(f"Config file must be a .json file: {config_path}")

    if not config_path.is_file():
        raise RuntimeError(f"Config file does not exist: {config_path}")

    try:
        with open(config_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Config file is not valid JSON: {config_path} ({e})")

    default_path = Path(__file__).parent.parent / "calibration.json"
    with open(default_path) as f:
        default = json.load(f)

    missing_keys = default.keys() - data.keys()
    if missing_keys:
        raise RuntimeError(f"User provided config file missing keys: {missing_keys}")


def _create_project_paths(project_dir):
    """Build the directories for the project."""

    project_path = Path(project_dir).expanduser().resolve()

    if project_path.exists():
        raise RuntimeError("Project directory already exists")

    project_path.mkdir()
    log(f"Created project workspace: {project_path}")
    
    jobs_path = project_path / "jobs"
    jobs_path.mkdir()
    log(f"Created jobs dir in workspace: {jobs_path}")

    conforms_path = project_path / "conforms"
    conforms_path.mkdir()
    log(f"Created conforms dir in workspace: {conforms_path}")

    return (project_path, jobs_path, conforms_path)


def _write_project_config(project_path: Path):
    """Write the project-level config.json file."""

    config = {
        
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
        #"residueTemplates": "Not implemented yet, see calibration _equalize_solvation.", 
        "ionCutoff":  0.5,
        "randomSeed": 12345,
    }

    config_path = project_path / "config.json"

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    log(f"Wrote project config: {config_path}")


def _create_manifest(project_path: Path):
    """Create the manifest.csv file."""

    manifest_path = project_path / "manifest.csv"

    with open(manifest_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["job_id", "structure_file"])

    log(f"Created manifest: {manifest_path}")


def _create_prep_script(project_path: Path):
    """ 
    Copy the default preparation script into
    the project for the user to modify
    """
    prep_script_path = project_path / "preparation_script.py"

    source = Path(__file__).resolve().parent.parent.parent / "prepDefaultDoNotModify.py"
    shutil.copy2(source, prep_script_path)

    log(f"Created preparation script: {prep_script_path}")








