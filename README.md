# trajseeder
A Python package to systematically prepare OpenMM simulations from an ensemble of protein structures

Early placeholder release to reserve the package namespace.
(This readme is currently outdated as implementation is ongoing. -Preston)

<details> <summary><strong>Overview</strong></summary>
          
**trajseeder** is a Python package for preparing large ensembles of protein structures for molecular dynamics simulation with OpenMM.

The primary goal of trajseeder is to transform an ensemble of experimentally or computationally derived protein conformations into a collection of **uniform, equilibrated simulation seeds** that are ready for large-scale distributed molecular dynamics.

Unlike traditional simulation setup tools that prepare one system at a time, trajseeder is designed to prepare **thousands to tens of thousands of systems** in a reproducible, automated, and statistically consistent manner.

## Motivation

Many modern molecular simulation workflows begin with an ensemble of structures obtained from various sources: 

* an NMR-derived ensembls (i.e. MODELs in a PDB file)
* cluster centers from conformational clustering of trajectory data
* Markov state model exemplars
* Generative AI models (e.g. BioEmu)

Preparing each structure individually often leads to subtle differences in solvent composition, box size, and equilibration protocol, making later comparisons between trajectories unnecessarily difficult.

trajseeder addresses this by applying a single, standardized preparation protocol across the entire ensemble.

## Design Philosophy

trajseeder separates the preparation workflow into three conceptual stages:

1. **Setup** build an initial file system to contain your project.
2. **Calibrate** solvate structures under equivalent conditions saving relevant information.
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
Input structure ensemble
          │
          ▼
   trajseeder plan
          │
          ▼
   modfiy calibration.json
          │
          ▼
   trajseeder calibrate
          │
          ▼
    <prepare jobs tbd>
          │
          ▼
 Project workspace
   ├── config.json
   ├── calibration.json
   ├── manifest.csv
   └── jobs/
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
    plan
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

trajseeder plan <TODO: something>

trajseeder run 0 --project my_project
```
</details>

<details> <summary><strong>Usage</strong></summary>

# Usage

trajseeder is designed around a staged workflow:

```text
setup → calibrate → plan → run → inspect/status/retry/verify
```

The intent is to separate **global ensemble setup** from **per-structure preparation jobs**.

### 1. Setup the file structure

First, trajseeder builds a standard file structure to keep your project organized.
This step creates a configuration file (config.json by default) or allows the user
to provide their own. The default file can be modified to fit the needs of your
simulation.

```bash
trajseeder setup structures/*.pdb
  --config_file config.json
  --project_dir trajseeder_project
```

### 2. Calibrate the solvent environment

Next, trajseeder uses provided input structures to allow the user to make informed decisions on size of
cannonical box. This decision along with config.json solvates all structures under the same conditions
and saves them to your project.

```bash
trajseeder calibrate trajseeder_project
```

This step is intended to determine parameters such as:

* canonical cubic box length
* target number of waters
* target number of ions
* solvent padding
* calibration metadata

The output is:

```text
calibration.json
```

This file records the ensemble-level solvent calibration used by later stages.

### 3. Plan a project workspace

Note: I am working on this step next, this probably isn't how I am going to implement it exactly.

Next, create a reproducible workspace containing one preparation job per input structure.

```bash
trajseeder plan structures/*.pdb \
  --calibration calibration.json \
  --project trajseeder_project
```

This creates a directory structure like:

```text
trajseeder_project/
├── config.json
├── calibration.json
├── manifest.csv
├── jobs/
│   └── 000/
│       ├── 000000/
│       │   ├── input.pdb
│       │   ├── config.json
│       │   └── status.txt
│       └── 000001/
│           ├── input.pdb
│           ├── config.json
│           └── status.txt
└── logs/
```

The project-level `config.json` stores simulation protocol settings such as force field files, timestep, constraints, nonbonded method, temperature, and pressure.

The `calibration.json` stores ensemble-derived solvent parameters.

The `manifest.csv` records the mapping between input structures and job IDs.

### 4. Run an individual preparation job

Each structure is prepared independently as a job.

```bash
trajseeder run 000123 --project trajseeder_project
```

A job will eventually perform the full preparation protocol:

```text
load input structure
build OpenMM topology/system
add solvent and ions
equalize water count
minimize energy
equilibrate under NPT conditions
serialize OpenMM system and state
```

Expected final outputs for a completed job are:

```text
jobs/000/000123/
├── input.pdb
├── config.json
├── status.txt
├── topology.pdb
├── system.xml
├── state.xml
└── job.log
```

The serialized `system.xml` and `state.xml` files are intended to be used later for production simulations on distributed computing platforms.

### 5. Run jobs on a cluster

trajseeder is designed to work naturally with scheduler array jobs.

For example, with SLURM:

```bash
#SBATCH --array=0-9999

trajseeder run $SLURM_ARRAY_TASK_ID --project trajseeder_project
```

Each job reads only its own job directory and writes only its own outputs, making the workflow safe for parallel execution.

### 6. Check project status

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

### 7. Inspect the ensemble

The `inspect` command is intended to provide quick diagnostics about the input structures.

```bash
trajseeder inspect structures/*.pdb
```

This may report information such as:

* number of structures
* structural extents
* approximate box-size requirements
* possible problematic input files

### 8. Retry failed jobs

Failed jobs can be reset for another attempt.

```bash
trajseeder retry-failed --project trajseeder_project
```

This command is intended to find jobs marked as `failed` and reset them to `pending`, or optionally emit a list of failed job IDs for resubmission.

### 9. Verify completed outputs

After a large preparation campaign, the `verify` command checks that outputs are present and readable.

```bash
trajseeder verify --project trajseeder_project
```

This command is intended to detect issues such as:

* missing `system.xml`
* missing `state.xml`
* incomplete job directories
* failed or unknown job states

### 10. Clean partial outputs

For development or failed campaign cleanup:

```bash
trajseeder clean --failed --project trajseeder_project
```

This command is intended to remove partial outputs from failed jobs while preserving inputs, configs, and status metadata.

## Typical Workflow

```bash

trajseeder setup structures/*.pdb

trajseeder calibrate trajseeder_project

trajseeder plan "this isn't implemented!"

trajseeder status --project trajseeder_project

trajseeder run 0 --project trajseeder_project

trajseeder verify --project trajseeder_project
```

For large ensembles, the `run` step is usually executed through a scheduler array rather than directly in a shell loop.

</details>
