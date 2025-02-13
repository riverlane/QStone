import re
from typing import List, Tuple, Dict
import numpy as np
from cuquantum import custatevec as cusv
import math

try:
    import cupy as cp
except ImportError:
    pass


class CudaSimulator:
    def __init__(self):
        # Standard gates and their matrix representations
        self.gates = {
            "x": np.array([[0, 1], [1, 0]], dtype=np.complex128),
            "h": 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]], dtype=np.complex128),
            "z": np.array([[1, 0], [0, -1]], dtype=np.complex128),
            "y": np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
            "s": np.array([[1, 0], [0, 1j]], dtype=np.complex128),
            "t": np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=np.complex128),
        }

        # Initialize CUDA handle
        self.handle = cusv.create()

    def parse_qasm(self, qasm_str: str) -> List[Tuple]:
        """Parse QASM string into list of operations"""
        circuit = []

        # Remove comments and empty lines
        lines = [line.split("//")[0].strip() for line in qasm_str.split("\n")]
        lines = [line for line in lines if line]

        # Skip header lines
        for line in lines:
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue

            if line.startswith("qreg"):
                # Extract number of qubits
                match = re.search(r"qreg\s+\w+\[(\d+)\]", line)
                if match:
                    self.num_qubits = int(match.group(1))
                continue

            # Parse gate applications
            gate_match = re.match(r"([a-z]+)\s+(q\[\d+\])", line)
            if gate_match:
                gate, qubit = gate_match.groups()
                qubit_idx = int(re.search(r"\[(\d+)\]", qubit).group(1))
                circuit.append((gate, qubit_idx))

            # Parse controlled gates
            cx_match = re.match(r"cx\s+q\[(\d+)\],\s*q\[(\d+)\]", line)
            if cx_match:
                control, target = map(int, cx_match.groups())
                circuit.append(("cx", control, target))

        return circuit

    def get_gate_matrix(self, gate: str) -> np.ndarray:
        """Get matrix representation of gate"""
        return self.gates.get(gate)

    def apply_gate(self, state_vec: cp.ndarray, gate: str, target: int):
        """Apply single-qubit gate to state vector"""
        gate_matrix = cp.asarray(self.get_gate_matrix(gate))
        cusv.apply_matrix(self.handle, state_vec, gate_matrix, [target])

    def apply_cx(self, state_vec: cp.ndarray, control: int, target: int):
        """Apply CNOT gate to state vector"""
        cx_matrix = cp.asarray(
            np.array(
                [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
                dtype=np.complex128,
            )
        )
        cusv.apply_matrix(self.handle, state_vec, cx_matrix, [control, target])

    def translate(self, qasm_str: str) -> cp.ndarray:
        """Translate QASM to cuQuantum and execute"""
        circuit = self.parse_qasm(qasm_str)

        # Initialize state vector
        state_vec = cp.zeros(2**self.num_qubits, dtype=cp.complex128)
        state_vec[0] = 1.0

        # Apply gates
        for operation in circuit:
            if operation[0] == "cx":
                _, control, target = operation
                self.apply_cx(state_vec, control, target)
            else:
                gate, target = operation
                self.apply_gate(state_vec, gate, target)

        return state_vec

    def __del__(self):
        """Clean up CUDA resources"""
        cusv.destroy(self.handle)
