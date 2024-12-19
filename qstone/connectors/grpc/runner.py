""" Quantum executor over a grpc channel """

import json
import secrets

import grpc

import qstone.connectors.grpc.qpu_pb2 as pb2
import qstone.connectors.grpc.qpu_pb2_grpc as pb2_grpc
from qstone.connectors import connection
from qstone.utils.utils import ComputationStep, QpuConfiguration, trace


class GRPCConnecction(connection.Connection):
    """Connection running jobs over gRPC"""

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.PRE,
    )
    def preprocess(self, qasm_ptr: str) -> str:
        # Currently passthrough.
        with open(qasm_ptr, "r", encoding="utf-8") as fid:
            return fid.read()

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.POST,
    )
    def postprocess(self, message: str) -> str:
        # Currently passthrough.
        print(f"postprocess: {message}")
        return json.loads(message)

    # mypy: disable-error-code="attr-defined"
    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.RUN,
    )
    def run(
        self, qasm_ptr: str, reps: int, host: str, server_port: int, lockfile: str
    ) -> dict:
        compression = None  # grpc.Compression.None
        # instantiate a channel
        channel = grpc.insecure_channel(
            f"{host}:{server_port}", compression=compression
        )
        stub = pb2_grpc.QPUStub(channel)
        pkt_id = secrets.randbelow(2**31)
        circuit = self.preprocess(qasm_ptr)
        request = pb2.Circuit(circuit=circuit, pkt_id=pkt_id)  # type: ignore[attr-defined]
        m = stub.RunQuantumCircuit(request)
        return self.postprocess(m.result)

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.QUERY,
    )
    def query_qpu_config(self, host: str, server_port: int) -> QpuConfiguration:
        """Query the Qpu configuraiton of the target"""
        print("implement me!")
        return QpuConfiguration()
