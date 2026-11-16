# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- quantum volume application
- faster and more modular generation of benchmarks
- dropped support for Python 3.10; minimum supported version is now 3.11
- removed `safety` from the `security` extra (it pins vulnerable `filelock<4.0`)
- moved `pip-audit` from runtime dependencies to the `security` extra
- added support for Python 3.13 and 3.14; the Rigetti connector (`pyquil`) is only available on Python 3.11 - 3.12
- relaxed the `numpy<2`, `stim==1.14.0` and `pyGSTi==0.9.13` pins, required for Python 3.13+
- added `grpcio` as an explicit dependency (previously only installed via `pyquil`)
- migrated packaging from Poetry to uv: PEP 621 metadata, `uv_build` backend and `uv.lock`
- moved the `test`, `lint`, `security` and `docs` extras to dependency groups; `mpi` remains an extra
- capped `pyquil<4.18`: newer releases depend on `jax`, which requires `numpy>=2` and conflicts with our `numpy<2` pin

## [0.2.1] - 2025-01-03

### Added

- github pages with basic and advanced usage examples plus API documentation.
- profile command now returns statistics as text

## [0.2.0] - 2025-14-01

### Fixed

- added extra checks on the config.json file. Now via json_schema

### Added

- support for scheduler mode.


## [0.1.0] - 2024-12-19

### Fixed

- removed spurious lock file
- corrected slurm sbatch flags

### Added

- assumptions. Defined the underlying assumptions of the benchmark.
- standard format for returning measurements in line with assumptions. Internal breaking changing - minor version bump.

## [0.0.3] - 2024-11-20

### Deprecated

- support for Python3.8
- automatic generation of all the scheduler. Only building now the one required.

### Fixed

- corrected the lock mechanism

### Added

- support for Rigetti backend
- flag to execute run step on a custom folder
- fail/success information in the json file
- example of gateway
- support for multiple folders for the profiler tool
- flag to generate an atomic job per application instead of splitting them over pre, run and post
- flag to generate a specific scheduler implementation
- separate timeout for http and lock mechanisms

## [0.0.2] - 2024-10-18

### Added

- first public drop, key functionalities to run custom and default apps to profile integration
