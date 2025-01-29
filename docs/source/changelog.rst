Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a
Changelog <https: keepachangelog.com="" en="" 1.1.0="">`__, and this project
adheres to `Semantic
Versioning <https: semver.org="" spec="" v2.0.0.html="">`__.

[Unreleased]
------------

-  quantum volume application
-  faster and more modular generation of benchmarks

[0.2.1] - 2025-01-28
--------------------

Added
~~~~~

-  Documentation via Sphinx


[0.2.0] - 2025-01-15
--------------------

Fixed
~~~~~

-  added extra checks on the config.json file. Now via json_schema

Added
~~~~~

-  support for scheduler mode.

[0.1.0] - 2024-12-19
--------------------

.. _fixed-1:

Fixed
~~~~~

-  removed spurious lock file
-  corrected slurm sbatch flags

.. _added-1:

Added
~~~~~

-  assumptions. Defined the underlying assumptions of the benchmark.
-  standard format for returning measurements in line with assumptions.
   Internal breaking changing - minor version bump.

.. _section-1:

[0.0.3] - 2024-11-20
--------------------

Deprecated
~~~~~~~~~~

-  support for Python3.8
-  automatic generation of all the scheduler. Only building now the one
   required.

.. _fixed-2:

Fixed
~~~~~

-  corrected the lock mechanism

.. _added-2:

Added
~~~~~

-  support for Rigetti backend
-  flag to execute run step on a custom folder
-  fail/success information in the json file
-  example of gateway
-  support for multiple folders for the profiler tool
-  flag to generate an atomic job per application instead of splitting
   them over pre, run and post
-  flag to generate a specific scheduler implementation
-  separate timeout for http and lock mechanisms

.. _section-2:

[0.0.2] - 2024-10-18
--------------------

.. _added-3:

Added
~~~~~

-  first public drop, key functionalities to run custom and default apps
   to profile integration
