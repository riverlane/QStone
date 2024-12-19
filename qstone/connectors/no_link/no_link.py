""" Runner for no-link connector"""

from qstone.connectors import connection
from qstone.utils.utils import (
    ComputationStep,
    QpuConfiguration,
    qasm_circuit_random_sample,
    trace,
)


class NoLinkConnection(connection.Connection):
    """No link connection running jobs without a server"""

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.PRE,
    )
    def preprocess(self, qasm_ptr: str) -> str:
        """Read QASM circuit files"""
        with open(qasm_ptr, "r", encoding="utf-8") as fid:
            qasm = fid.read()
        return qasm

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.PRE,
    )
    def postprocess(self, message: str) -> dict:
        # Currently passthrough.
        # generate one random entry with correct number of shots
        # REVISIT(mghibaudi, "use self.num_qubits to generate the values")
        return {"00": 0, "01": 0, "10": 0, "11": 0}

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.POST,
        label="get_outcomes",
    )
    def _get_outcomes(self, qasm_circuit: str, reps: int) -> dict:
        return qasm_circuit_random_sample(qasm_circuit, reps)

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.POST,
    )
    def run(
        self, qasm_ptr: str, reps: int, host: str, server_port: int, lockfile: str
    ) -> dict:
        """Local simulated run of circuit"""
        qasm_circuit = self.preprocess(qasm_ptr)
        outcomes = qasm_circuit_random_sample(qasm_circuit, reps)
        return outcomes
