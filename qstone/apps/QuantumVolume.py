"""Defines the two steps of PyMatching jobs"""

import os
from typing import Dict, List

import numpy as np
import pymatching
from pandera import Check, Column, DataFrameSchema

import random
from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace

try:
    from qstone.simulators.cuda_sim import CudaSim
except:
    from qstone.simulators.qutip_sim import QuTiPSim


class QuantumVolume(Computation):
    """
    PyMatching computation class.
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
        self.num_qubits = int(os.environ.get("NUM_QUBITS", self.num_qubits))
        self.results = None

    def _random_sampling(self, num_qubits) -> str:
        """Generate a circuit random sampling"""
        gates = []
        for _ in range(num_qubits):
            # Single qubit gate
            for i in range(num_qubits):
                q1_gate = random.choices(["RX", "RY", "RZ"])
                theta = random.random()
                gates.append(f"{q1_gate} {i} {theta}")

            nums = random.sample(range(num_qubits), num_qubits)
            q2_gates = list(zip(nums[: n // 2], nums[n // 2 :]))
            gates.append(f"CZ {', '.join(q2_gates)}")
            gates.append("barrier")
        return gates

    def _generate_circuit(self, num_qubits) -> str:
        """Initialise the square circuit of size num_qubits"""

        while hops < 0.66:
            gates = _random_sampling(num_qubits)
            hops = _compute_hop(circuit)
        return (circuit, hops)

    #    def _compute_hop(self, qasm) -> str:

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """Prepare and write circuit for QEC experiment

        Args:
            datapath: path location to write circuit

        Returns: path location of written circuit, without extension
        """
        for i in range(self.num_qubits):
            circuit = _generate_circuit()
            print(f"datapath: {datapath}")
            circuit_path = os.path.join(
                datapath, f"QuantumVolume_q{self.num_qubits}_{os.environ['JOB_ID']}"
            )

            # Write qasm circuit
            with open(f"{circuit_path}.qasm", "w", encoding="utf-8") as fid:
                fid.write(str(qasm_circuit))

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
        self.results = {}
        for i in range(self.num_qubits):
            circuit_path = os.path.join(
                datapath, f"QuantumVolume_q{i}_{os.environ['JOB_ID']}"
            )
            # Send circuit to connector
            results.append(
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
