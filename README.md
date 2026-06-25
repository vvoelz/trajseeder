# trajseeder
A Python package to systematically prepare OpenMM simulations from an ensemble of protein structures

Early placeholder release to reserve the package namespace.


# trajseeder

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

1. **Calibrate** the solvent environment using a representative subset of structures.
2. **Plan** a reproducible project workspace containing one preparation job for every input structure.
3. **Run** each preparation job independently to produce equilibrated OpenMM simulation seeds.

Each preparation job:

* constructs the molecular system
* adds solvent and ions
* minimizes the structure
* equilibrates under NPT conditions
* serializes the resulting OpenMM system and state

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
   trajseeder calibrate
          │
          ▼
   calibration.json
          │
          ▼
      trajseeder plan
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
