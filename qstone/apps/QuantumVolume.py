"""Defines the Quantum Volume application"""

import os
from typing import Dict, List, Tuple

import numpy as np
from pandera import Check, Column, DataFrameSchema

import random
from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace

try:
    from qstone.simulators.cuda_qsim import CudaSim as Sim
except ImportError:
    from qstone.simulators.qutip_qsim import QuTiPSim as Sim


class QuantumVolume(Computation):
    """
    QuantumVolume computation class.
    """

    COMPUTATION_NAME = "QuantumVolume"
    CFG_STRING = """
    {
      "cfg":
      {
        "num_required_qubits" : 10,
        "repetitions": 2
      }
    }
    """
    SCHEMA = DataFrameSchema(
        {
            "repetitions": Column(int, Check(lambda s: s >= 0)),
        }
    )

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        # Hints - do not remove
        self.repetitions: int
        self.num_shots = int(os.environ.get("NUM_SHOTS", self.repetitions))
        self.num_qubits = int(os.environ.get("NUM_QUBITS", 2))
        self.results = None

    def _random_sampling(self, num_qubits) -> str:
        """Generate a circuit random sampling"""
        circuit = f"OPENQASM 2.0;\n"
        circuit += 'include "qelib1.inc";\n'
        circuit += f"CREG C[{num_qubits}];\n"
        circuit += f"QREG Q[{num_qubits}];\n"
        for i in range(num_qubits):
            # Single qubit gate
            for i in range(num_qubits):
                q1_gate = random.choices(["RX", "RY", "RZ"])
                theta = random.random()
                circuit += f"{q1_gate[0]}({theta}) Q[{i}];\n"
            nums = random.sample(range(num_qubits), num_qubits)
            q2_gates = list(zip(nums[: num_qubits // 2], nums[num_qubits // 2 :]))
            for q2s in q2_gates:
                circuit += f"CX Q[{q2s[0]}], Q[{q2s[1]}];\n"
        for i in range(num_qubits):
            circuit += f"MEASURE Q[{i}] -> C[{i}];\n"
        return circuit

    def _generate_circuit(self, num_qubits) -> str:
        """Initialise the square circuit of size num_qubits"""
        hops = 0
        print("_generate_circuit")
        while hops < 0.66:
            circuit = self._random_sampling(num_qubits)
            print(f"{circuit=}")
            hops, results = self._compute_hop(circuit)

        return (circuit, hops)

    def _compute_hop(self, qasm) -> tuple[float, List]:
        results = Sim().run(qasm, 100)
        print(f"{results=}")
        values = [sum(x) for x in zip(*results)]
        print(f"{values=}")
        assert results == 0

        return (0.67, results)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """Prepare and write circuit for QEC experiment

        Args:
            datapath: path location to write circuit

        Returns: path location of written circuit, without extension
        """
        print(f"pre - {self.num_qubits}")
        for i in range(2, self.num_qubits):
            print(f"datapath: {datapath}")
            circuit = self._generate_circuit(i)
            print(f"datapath: {datapath}")
            circuit_path = os.path.join(
                datapath, f"QuantumVolume_q{self.num_qubits}_{os.environ['JOB_ID']}"
            )

            # Write qasm circuit
            with open(f"{circuit_path}.qasm", "w", encoding="utf-8") as fid:
                fid.write(str(circuit))

        return circuit_path

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.RUN)
    def run(self, datapath: str, connection: connector.Connector):
        """Runs the Quantum circuit N times

        Args:
            datapath: path location to write circuit
            connection: connector object to run circuit
            shots: number of shots to be executed

        Returns: path location of syndromes file
        """
        self.results = []
        for i in range(self.num_qubits):
            circuit_path = os.path.join(
                datapath, f"QuantumVolume_q{i}_{os.environ['JOB_ID']}"
            )
            # Send circuit to connector
            self.results.append(
                connection.run(qasm=f"{circuit_path}.qasm", reps=self.num_shots)
            )

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Runs the postprocessing analysis to obtain volume

        Args:
            datapath: path location to write circuit

        Returns: quantum volume
        """

        for i in range(self.num_qubits):
            circuit_path = os.path.join(
                datapath, f"QuantumVolume_q{i}_{os.environ['JOB_ID']}"
            )
            # Run simulation and get back results
            # Compare results
            # self.results[i] =
        return num_errors
