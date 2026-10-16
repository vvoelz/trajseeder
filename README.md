# trajseeder
A Python package to systematically prepare OpenMM simulations from an ensemble of protein structures

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

1. **Setup** an initial file system to contain your project.
2. **Calibrate** equivalent conditions and solvate structures, saving relevant information and populating jobs.
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
 <modfiy calibration.json>
 <modify preparation_script.py>
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

Trajseeder is under active development. Please submit features you would like to see or bugs you have come across
to our github issues page.

</details> 

<details> <summary><strong>Installation</strong></summary>

## Installation

### Requirements

trajseeder is written for Python 3.11 or later and is built around the OpenMM molecular simulation toolkit.

Current dependencies include:

* OpenMM (openmm.org)
* MDTraj (mdtraj.org)
* NumPy
* SciPy
* Typer
* rich
* tqdm

### Install from PyPI

The latest released version can be installed with:

```bash
pip install trajseeder
```

### Install from source

To install the latest development version:

```bash
git clone https://github.com/vvoelz/trajseeder.git
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
    retry-failed
    verify
    clean
```

</details> 


<details> <summary><strong>Quick start</strong></summary>

# Quick start
```
trajseeder setup structures/*.pdb

trajseeder calibrate trajseeder_project

trajseeder run trajseeder_project 0
```
</details>

<details> <summary><strong>Usage</strong></summary>

# Usage

Trajseeder is designed around a staged workflow:

```text
setup → calibrate → run → inspect/status/retry/verify
```

The intent is to separate **global ensemble setup** from **per-structure preparation jobs**.

### 1. Setup the file structure

First, trajseeder builds a standard file structure to keep your project organized
and import the structures you will be working with. **It is assumed these structures are clean pdb files, all representing different conformations of the same molecule. Trajseeder does not clean or repair structures for you.**
This step creates a configuration file (config.json) or allows the user
to provide their own. The default file can be easily modified to fit the needs of your
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
└─── jobs/
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
* number of waters
* number of positive ions
* number of negative ions
* other calibration metadata

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
prepare the simulation seeds for use. Each job reads only its own job directory and writes only its own outputs, making the workflow safe for parallel execution. Trajseeder provides various executors to determine how this process is done:

**default-serial** - Runs jobs one after another on your machine's default hardware.

**default-parallel** - [Work in progress]

**slurm** - [Work in progress]


```bash
trajseeder run trajseeder_project --all --executor default-serial
trajseeder run trajseeder_project 0 1 2 3 --executor default-serial
```

A job will eventually perform the full preparation protocol, by default:

```text
load solvated input structure
build OpenMM topology/system
minimize energy
equilibrate under NVT and NPT conditions
serialize OpenMM system and state
```
This preparation protocol can be found in the folder you created with trajseeder setup.
It contains instructions for how to modify it to your liking, and includes logging functionality
so you can keep track of whatever you need.

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


### 4. Check project status

To summarize job progress:

```bash
trajseeder status trajseeder_project
```

Example output:

```text
PENDING: 4213
RUNNING: 81
COMPLETE: 2900
FAILED: 16
```

Job status is tracked using simple `status.txt` files inside each job directory.
Pending jobs have not been touched by run yet, either because of a delay in execution such as the serial case,
or because they have not been called with trajseeder run at all.

### 5. Clean partial outputs

For failed job cleanup:

```bash
trajseeder clean trajseeder_project
```
This command is intended to find jobs marked as `failed` and reset them to `pending` while preserving inputs, configs, and status metadata.

### 6. Retry failed jobs

Failed jobs can be run immediately for another attempt.

```bash
trajseeder retry-failed trajseeder_project --executor default-serial
```
This command is intended to find jobs marked as `failed`, clean them up, and re-run them immediately.

### 7. Verify completed outputs

After a large preparation campaign, the `verify` command checks that outputs are present and readable.

```bash
trajseeder verify trajseeder_project
```

This command is intended to detect issues such as:

* missing `system.xml`
* missing `state.xml`
* incomplete job directory
* failed or unknown job states

These checks are being acitvely developed and improved. If you notice trajseeder is producing problematic outputs,
please report them to us so we can make our verification more robust.

## Typical Workflow

```bash

trajseeder setup structures/*.pdb --project-dir trajseeder_project

<Modify config.json and preparation_script.py>

trajseeder calibrate trajseeder_project

trajseeder run trajseeder_project --all --executor default-serial

trajseeder status trajseeder_project

trajseeder verify trajseeder_project
```

For large ensembles, the `run` step is usually executed through a scheduler array rather than directly in a shell loop.

</details>
