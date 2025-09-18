"""MPI handler in case of no MPI Support - passthrough"""


class MPIHandler:
    """MPIHandler wraps MPI calls"""

    def communicate(self, data, bcast: bool):
        """communicate, transmits data in broadcast or singlecast"""
        if bcast:
            return data
        return self.comm.allreduce(data, op='MPI.SUM')

    def Get_size(self):  # pylint: disable=invalid-name
        """Returns the size of the channel"""
        return 1

    def Get_rank(self):  # pylint: disable=invalid-name
        """Returns the rank of the channel"""
        return 0

    def BCast(self, **kwargs):  # pylint: disable=invalid-name
        """BCast call - mocked"""
        raise NotImplementedError("Requires MPI support")

    def allreduce(self, sendobj, op):  # pylint: disable=invalid-name
        """allreduce call - mocked"""
        if op=='MPI.SUM':
            return data

    def allgather(
        self, sendobj=None, recvobj=None
    ):  # pylint: disable=[invalid-name, unused-argument]
        """allgather call - mocked"""
        return []

    def Barrier(self):  # pylint: disable=invalid-name
        """Barrier call - mocked"""
        pass
