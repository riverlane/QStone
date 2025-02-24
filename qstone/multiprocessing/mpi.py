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

    def Get_size(self) -> int:  # pylint: disable=invalid-name
        """Redirects call to MPI Get_size"""
        return self.comm.Get_size()

    def Get_rank(self) -> int:  # pylint: disable=invalid-name
        """Redirects call to MPI Get_rank"""
        return self.comm.Get_rank()

    def Barrier(self):  # pylint: disable=invalid-name
        """Redirects call to MPI Barrier"""
        return self.comm.Barrier()

    def allgather(self, sendobj):  # pylint: disable=invalid-name
        """Redirects call to MPI allgather"""
        return self.comm.allgather(sendobj)
