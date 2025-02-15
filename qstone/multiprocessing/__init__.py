"""Wrapper for MPI calls"""

try:
    from qstone.multiprocessing.mpi import MPIHandler
except ModuleNotFoundError:
    from qstone.multiprocessing.nompi import MPIHandler
