""" Connectors for different Quantum Stacks """

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
        host: str,
        server_port: int,
        lockfile: Optional[str],
    ):
        """Initialise the connector object"""
        self._protocol = conn_type
        self._host = host
        self._server_port = server_port
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
    def host(self):
        """Returns the host name"""
        return self._host

    @property
    def server_port(self):
        """Returns the server_port"""
        return self._server_port

    @property
    def connection(self):
        """Returns the server_port"""
        return self._connection

    @property
    def address(self):
        """Returns the address of the Quantum bridge device"""
        return f"{self.host}::{self.server_port}"

    @property
    def lockfile(self):
        """Returns the lockfile information"""
        return self._lockfile

    def run(self, qasm: str, reps: int):
        """Runs the provided QASM circuit"""
        return self.connection.run(
            qasm, reps, self.host, self.server_port, self.lockfile
        )
