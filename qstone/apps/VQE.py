"""VQE computations steps."""

import os
import time

import numpy
from pandera import Check, Column, DataFrameSchema

from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace


class VQE(Computation):
    """
    VQE computation class.
    """

    COMPUTATION_NAME = "VQE"
    CFG_STRING = """
    {
      "cfg":
      {
        "num_required_qubits" : 4,
        "repetitions" : 10,
        "iterations" : 10,
        "compute_duration" : 1
      }
    }
    """
    SCHEMA = DataFrameSchema(
        {
            "repetitions": Column(int, Check(lambda s: s >= 0)),
            "iterations": Column(int, Check(lambda s: s >= 0)),
            "compute_duration": Column(int, Check(lambda s: s >= 0)),
        }
    )

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        # Hints - do not remove
        self.repetitions: int
        self.iterations: int
        self.compute_duration: int
        self.num_shots = int(os.environ.get("NUM_SHOTS", self.repetitions))

    def _generate_circuit(self, datapath: str, num_qubits: int):
        """Generate a random (small) quantum circuit"""
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";'
        qasm += f"\nqreg q[{num_qubits}];\ncreg c[{num_qubits}];"
        # Add N rounds of gates.
        for i in range(numpy.random.randint(4, 20)):
            qasm += numpy.random.choice(
                [
                    f"rx({i/4}) q[{i%num_qubits}];\n",
                    f"rz({i/3}) q[{i%num_qubits}];\n",
                    f"h q[{i%num_qubits}];\n",
                ]
            )
        # Reading all qubit states
        for i in range(num_qubits):
            qasm += f"measure q[{i}] -> c[{i}];\n"
        # Write it back
        with open(
            f"{os.path.join(datapath, 'random')}.qasm", "w", encoding="utf-8"
        ) as fid:
            fid.write(qasm)
        print(f"Generated VQE-like circuit with {num_qubits} qubits")

    def _mock_compute(self):
        """Function that mimics computation delay. Simple sleep of constant duration."""
        time.sleep(self.compute_duration / 1000)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """Phase not required"""

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.RUN)
    def run(self, datapath: str, connection: connector.Connector):
        """Runs the Quantum circuit N times"""
        # Executing self.iterations iterations with a maximum of self.repetitions shots each
        for _ in range(numpy.random.randint(1, self.iterations)):
            self._generate_circuit(datapath, int(os.environ["NUM_QUBITS"]))
            connection.run(
                qasm=f"{os.path.join(datapath, 'random')}.qasm", reps=self.num_shots
            )
            self._mock_compute()

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Phase not required"""
