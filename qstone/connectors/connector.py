"""Connectors for different Quantum Stacks"""

import warnings
from enum import Enum
from typing import Optional

from qstone.connectors import connection

try:
    from qstone.connectors.grpc.runner import GRPCConnecction
except ImportError:
    warnings.warn("grpc failed to import", ImportWarning)
from qstone.connectors.backends.rigetti.runner import RigettiConnection
from qstone.connectors.http.runner import HttpConnection
from qstone.connectors.no_link.no_link import NoLinkConnection


class ConnectorType(Enum):
    """Type of connection"""

    GRPC = "GRPC"
    NO_LINK = "NO_LINK"
    HTTPS = "HTTPS"
    RIGETTI = "RIGETTI"


class Connector:
    """Class used to hold connection between HPC compute node and Quantum bridge"""

    def __init__(
        self,
        conn_type: ConnectorType,
        mode: str,
        qpu_host: str,
        qpu_port: int,
        compiler_host: str,
        compiler_port: int,
        target: str,
        lockfile: Optional[str],
    ):
        """Initialise the connector object"""
        self._protocol = conn_type
        self._mode = mode
        self._qpu_host = qpu_host
        self._qpu_port = qpu_port
        self._compiler_host = compiler_host
        self._compiler_port = compiler_port
        self._target = target
        self._connection: connection.Connection
        self._lockfile: Optional[str] = None if lockfile == "NONE" else lockfile

        if self.protocol == ConnectorType.GRPC:
            self._connection = GRPCConnecction()
        elif self.protocol == ConnectorType.HTTPS:
            self._connection = HttpConnection()
        elif self.protocol == ConnectorType.NO_LINK:
            self._connection = NoLinkConnection()
        elif self.protocol == ConnectorType.RIGETTI:
            self._connection = RigettiConnection()

    @property
    def protocol(self):
        """Returns the protocol information"""
        return self._protocol

    @property
    def mode(self):
        """Returns the mode in use (EMULATION, REAL, RANDOM)"""
        return self._mode

    @property
    def qpu_host(self):
        """Returns the qpu host name"""
        return self._qpu_host

    @property
    def qpu_port(self):
        """Returns the qpu port"""
        return self._qpu_port

    @property
    def compiler_host(self):
        """Returns the compiler host name"""
        return self._compiler_host

    @property
    def compiler_port(self):
        """Returns the compiler_port"""
        return self._compiler_port

    @property
    def connection(self):
        """Returns the server_port"""
        return self._connection

    @property
    def address(self):
        """Returns the address of the Quantum bridge device"""
        return f"{self.qpu_host}::{self.qpu_port}"

    @property
    def target(self):
        """Returns the target name"""
        return self._target

    @property
    def lockfile(self):
        """Returns the lockfile information"""
        return self._lockfile

    def run(self, qasm: str, reps: int):
        """Runs the provided QASM circuit"""
        return self.connection.run(
            qasm,
            reps,
            self.mode,
            self.qpu_host,
            self.qpu_port,
            self.compiler_host,
            self.compiler_port,
            self.target,
            self.lockfile,
        )
