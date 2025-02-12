"""Simulation abstract class"""

from abc import ABC, abstractmethod
import re
from typing import List, Tuple


class Simulation(ABC):
    """Simulation abstract class"""

    def parse_qasm(self, qasm_str: str) -> List[Tuple]:
        """Parse QASM string into list of operations"""
        circuit = []

        # Remove comments and empty lines
        lines = [line.split("//")[0].strip() for line in qasm_str.split("\n")]
        lines = [line.lower() for line in lines if line]

        for line in lines:
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue

            if line.startswith("qreg"):
                match = re.search(r"qreg\s+\w+\[(\d+)\]", line)
                if match:
                    self.num_qubits = int(match.group(1))
                continue

            if line.startswith("creg"):
                match = re.search(r"creg\s+(\w+)\[(\d+)\]", line)
                if match:
                    reg_name, size = match.groups()
                    self.measurements[reg_name] = [None] * int(size)
                continue

            # Parse measurements
            measure_match = re.match(
                r"measure\s+q\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]", line
            )
            if measure_match:
                qubit, reg, bit = measure_match.groups()
                circuit.append(("measure", int(qubit), reg, int(bit)))
                continue

            # Parse rotation gates
            rot_match = re.match(r"(rx|ry|rz)\(([^)]+)\)\s+q\[(\d+)\]", line)
            if rot_match:
                gate, angle, qubit = rot_match.groups()
                # Convert angle to float (handle pi notation)
                angle = float(eval(angle.replace("pi", "np.pi")))
                circuit.append((gate, angle, int(qubit)))
                continue

            # Parse CNOT gates
            cx_match = re.match(r"cx\s+q\[(\d+)\],\s*q\[(\d+)\]", line)
            if cx_match:
                control, target = map(int, cx_match.groups())
                circuit.append(("cx", control, target))
                continue

            # Parse standard gates
            gate_match = re.match(r"([a-z]+)\s+(q\[\d+\])", line)
            if gate_match:
                gate, qubit = gate_match.groups()
                qubit_idx = int(re.search(r"\[(\d+)\]", qubit).group(1))
                circuit.append((gate, qubit_idx))
                continue

        return circuit

    @abstractmethod
    def run(self, qasm: str) -> []:
        """Runs a quantum circuit"""
        raise NotImplementedError
