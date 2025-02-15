"""MPI wrapper module"""

from mpi4py import MPI  # pylint: disable=import-error


class MPIHandler:
    """MPIHandler class to wrap the MPI calls"""

    def __init__(self):
        self.comm = MPI.COMM_WORLD

    def communicate(self, data, bcast: bool):
        """communicate, transmits data in broadcast or singlecast"""
        if bcast:
            return self.comm.Bcast([data, MPI.DOUBLE], root=0)
        return self.comm.allreduce(data, op=MPI.SUM)
