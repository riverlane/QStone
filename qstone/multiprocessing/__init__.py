"""Wrapper for MPI calls"""

try:
    from qstone.multiprocessing.mpi import MPIHandler  # type: ignore [assignment]
except ModuleNotFoundError:
    from qstone.multiprocessing.nompi import MPIHandler  # type: ignore [assignment]
