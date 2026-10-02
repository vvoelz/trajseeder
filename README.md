# trajseeder
A Python package to systematically prepare OpenMM simulations from an ensemble of protein structures

Early placeholder release to reserve the package namespace.

(This readme will be perpetually outdated, and may contain my personal notes leading up to release 1.0 as implementation is ongoing. -Preston)

<details> <summary><strong>Overview</strong></summary>
          
**trajseeder** is a Python package for preparing large ensembles of protein structures for molecular dynamics simulation with OpenMM.

The primary goal of trajseeder is to transform an ensemble of experimentally or computationally derived protein conformations into a collection of **uniform, equilibrated simulation seeds** that are ready for large-scale distributed molecular dynamics.

Unlike traditional simulation setup tools that prepare one system at a time, trajseeder is designed to prepare **thousands to tens of thousands of systems** in a reproducible, automated, and statistically consistent manner.

## Motivation

Many modern molecular simulation workflows begin with an ensemble of structures obtained from various sources: 

* an NMR-derived ensembles (i.e. MODELs in a PDB file)
* cluster centers from conformational clustering of trajectory data
* Markov state model exemplars
* Generative AI models (e.g. BioEmu)

Preparing each structure individually often leads to subtle differences in solvent composition, box size, and equilibration protocol, making later comparisons between trajectories unnecessarily difficult.

trajseeder addresses this by applying a single, standardized preparation protocol across the entire ensemble.

## Design Philosophy

trajseeder separates the preparation workflow into three conceptual stages:

1. **Setup** build an initial file system to contain your project.
2. **Calibrate** solvate structures under equivalent conditions saving relevant information and populating jobs.
3. **Run** each preparation job independently to produce equilibrated OpenMM simulation seeds.


Each calibration job:

* constructs the molecular system
* establishes a cannonical box length
* adds the same number of solvent and ions to each box

The resulting outputs are intended to serve as **starting points for production simulations**, which may be executed later on HPC clusters or distributed computing platforms.

## Features

* Automated preparation of large structural ensembles
* Reproducible project workspaces
* Uniform solvent composition across all systems
* Standardized equilibration protocol
* Independent, restartable preparation jobs
* HPC-friendly filesystem layout with job sharding
* Native OpenMM serialization for downstream simulation

## Workflow

```text

   trajseeder setup
          │
          ▼
 modfiy calibration.json
 modify preparation_script.py
          │
          ▼
  trajseeder calibrate
          │
          ▼
    trajseeder run
          │
          ▼
Equilibrated OpenMM simulation seeds
          │
          ▼
Distributed production simulations
```

## Current Status

trajseeder is under active development. The current focus is on building a robust, modular framework for large-scale OpenMM system preparation before implementing the full simulation protocol.


</details> 

<details> <summary><strong>Installation</strong></summary>

## Installation

### Requirements

trajseeder is written for Python 3.10 or later and is built around the OpenMM molecular simulation toolkit.

Current dependencies include:

* OpenMM (openmm.org)
* MDTraj (mdtraj.org)
* NumPy
* Typer (command-line interface)
* tqdm
* TODO: ensure all dependencies are listed and reflected in toml file

Additional scientific Python packages may be added as development continues.

### Install from PyPI

The latest released version can be installed with:

```bash
pip install trajseeder
```

### Install from source

To install the latest development version:

```bash
git clone https://github.com/<your-github-username>/trajseeder.git
cd trajseeder

pip install -e .
```

The editable (`-e`) installation is recommended for developers, as changes to the source code are immediately reflected without reinstalling the package.

### Verify the installation

After installation, the command-line interface should be available:

```bash
trajseeder --help
```

which displays the available commands:

```text
Usage: trajseeder [OPTIONS] COMMAND [ARGS]...

Commands:
    setup
    calibrate
    run
    status
    inspect
    retry-failed
    verify
    clean
```

### Development status

trajseeder is currently under active development. The overall project architecture is subject to change leading up to release 1.0 while the OpenMM preparation protocol is still being implemented.

Interfaces may evolve as the project matures.

</details> 


<details> <summary><strong>Quick start</strong></summary>

# Quick start
```

trajseeder setup structures/*.pdb

trajseeder calibrate trajseeder_project

trajseeder run trajseeder_project --all
```
</details>

<details> <summary><strong>Usage</strong></summary>

# Usage

trajseeder is designed around a staged workflow:

```text
setup → calibrate → run → inspect/status/retry/verify
```

The intent is to separate **global ensemble setup** from **per-structure preparation jobs**.

### 1. Setup the file structure

First, trajseeder builds a standard file structure to keep your project organized
and import the structures you will be working with.
This step creates a configuration file (config.json) or allows the user
to provide their own. The default file can be modified to fit the needs of your
simulation.
This step also creates preparation_script.py, a script outlining a standard
openMM protocol to be applied to all solvated conforms in a later step. 
This file can be modified according to the user's wishes.

```bash
trajseeder setup structures/*.pdb
  --config_file config.json
  --project_dir trajseeder_project
```
The result is a file tree like this:

```text
trajseeder_project/
├── config.json
├── manifest.csv
├── preparation_script.py
├── conforms/
│    ├── structure_a.pdb
│    ├── structure_b.pdb
│    └── structure_c.pdb
├── jobs/
└── logs/
```
`config.json` stores project-level simulation protocol settings such as force field files, timestep, constraints, nonbonded method, temperature, and pressure.

`manifest.csv` records the mapping between input structures and job IDs.

`preparation_script.py` outlines a standard openMM protocol to be applied to all solvated conforms. It is able to be modified.

### 2. Calibrate the solvent environment

Next, trajseeder uses provided input structures to allow the user to make informed decisions on size of
cannonical box. This decision along with config.json solvates all structures under the same conditions
and saves them as jobs to your project. The information on how they were solvated is saved to calibration.json.

```bash
trajseeder calibrate trajseeder_project
```

This step is intended to determine parameters such as:

* canonical cubic box length
* target number of waters
* target number of ions
* solvent padding
* calibration metadata

The project is updated:

```text
trajseeder_project/
├── config.json
├── calibration.json
├── manifest.csv
├── conforms/
│    ├── structure_a.pdb
│    ├── structure_b.pdb
│    └── structure_c.pdb
├── jobs/
│    ├── 000001/
│    │   ├── input.pdb
│    │   └── status.txt
│    ├── 000002/
│    │   ├── input.pdb
│    │   └── status.txt
│    └── 000003/
│        ├── input.pdb
│        └── status.txt
└── logs/
```

`calibration.json` stores ensemble-derived solvent parameters.

Each project is intended to have one unique config.json, calibration.json, manifest.csv, preparation_script.py and, at most one job per
structure.


### 3. Run preparation jobs

Now that each conformation has been solvated, a standard protocol needs to be run on each of them to
prepare the for simulation on HPC or distributed computing. Trajseeder provides various executors to 
determine how this process is done. Currently only default-serial is available, which runs jobs one 
after another. 

TODO: make help explain options and write a quick summary of them here.


```bash
trajseeder run trajseeder_project --all --executor default-serial
trajseeder run trajseeder_project 1 2 3 --executor default-serial
```

A job will eventually perform the full preparation protocol, by default:

```text
load solvated input structure
build OpenMM topology/system
minimize energy
equilibrate under NVT and NPT conditions
serialize OpenMM system and state
```

Expected final outputs for a completed job are:

```text
jobs/000123/
├── input.pdb
├── status.txt
├── topology.pdb
├── system.xml
├── state.xml
└── job.log
```

The serialized `system.xml` and `state.xml` files are intended to be used later for production simulations on distributed computing platforms.

### 4. Run jobs on a cluster

trajseeder is designed to work naturally with scheduler array jobs.

For example, with SLURM:

```bash
#SBATCH --array=0-9999

trajseeder run $SLURM_ARRAY_TASK_ID --project trajseeder_project
```

Each job reads only its own job directory and writes only its own outputs, making the workflow safe for parallel execution.

### 5. Check project status

To summarize job progress:

```bash
trajseeder status --project trajseeder_project
```

Example output:

```text
pending: 4213
running: 84
complete: 5680
failed: 23
```

Job status is tracked using simple `status.txt` files inside each job directory.

### 6. Inspect the ensemble

The `inspect` command is intended to provide quick diagnostics about the input structures.

```bash
trajseeder inspect structures/*.pdb
```

This may report information such as:

* number of structures
* structural extents
* approximate box-size requirements
* possible problematic input files

### 7. Retry failed jobs

Failed jobs can be reset for another attempt.

```bash
trajseeder retry-failed --project trajseeder_project
```

This command is intended to find jobs marked as `failed` and reset them to `pending`, or optionally emit a list of failed job IDs for resubmission.

### 8. Verify completed outputs

After a large preparation campaign, the `verify` command checks that outputs are present and readable.

```bash
trajseeder verify --project trajseeder_project
```

This command is intended to detect issues such as:

* missing `system.xml`
* missing `state.xml`
* incomplete job directories
* failed or unknown job states

### 9. Clean partial outputs

For development or failed campaign cleanup:

```bash
trajseeder clean --failed --project trajseeder_project
```

This command is intended to remove partial outputs from failed jobs while preserving inputs, configs, and status metadata.

## Typical Workflow

```bash

trajseeder setup structures/*.pdb

trajseeder calibrate trajseeder_project

trajseeder status --project trajseeder_project

trajseeder run 0 --project trajseeder_project

trajseeder verify --project trajseeder_project
```

For large ensembles, the `run` step is usually executed through a scheduler array rather than directly in a shell loop.

</details>
