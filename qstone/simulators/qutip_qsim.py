import re
from typing import List, Tuple, Dict
import numpy as np
import qutip as qt
from qstone.simulators.simulation import Simulation


class QuTiPSim(Simulation):
    def __init__(self):
        # Standard single-qubit gates as QuTiP operators
        self.gates = {
            "x": qt.sigmax(),
            "y": qt.sigmay(),
            "z": qt.sigmaz(),
            "h": qt.Qobj([[1, 1], [1, -1]]) / np.sqrt(2),
            "s": qt.Qobj([[1, 0], [0, 1j]]),
            "t": qt.Qobj([[1, 0], [0, np.exp(1j * np.pi / 4)]]),
        }

    def rx(self, theta: float) -> qt.Qobj:
        """Create Rx rotation gate"""
        return qt.Qobj(
            [
                [np.cos(theta / 2), -1j * np.sin(theta / 2)],
                [-1j * np.sin(theta / 2), np.cos(theta / 2)],
            ]
        )

    def ry(self, theta: float) -> qt.Qobj:
        """Create Ry rotation gate"""
        return qt.Qobj(
            [
                [np.cos(theta / 2), -np.sin(theta / 2)],
                [np.sin(theta / 2), np.cos(theta / 2)],
            ]
        )

    def rz(self, theta: float) -> qt.Qobj:
        """Create Rz rotation gate"""
        return qt.Qobj([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]])

    def apply_single_qubit_gate(
        self, gate: str, qubit: int, theta: float = None
    ) -> qt.Qobj:
        """Create QuTiP operator for single-qubit gate"""
        ops = [qt.qeye(2)] * self.num_qubits

        if gate in ["rx", "ry", "rz"]:
            if gate == "rx":
                ops[qubit] = self.rx(theta)
            elif gate == "ry":
                ops[qubit] = self.ry(theta)
            else:  # rz
                ops[qubit] = self.rz(theta)
        else:
            ops[qubit] = self.gates[gate]

        return qt.tensor(ops)

    def apply_cnot(self, control: int, target: int) -> qt.Qobj:
        """Create QuTiP operator for CNOT gate"""
        ops = []
        for i in range(self.num_qubits):
            if i == control:
                ops.append(
                    qt.basis([2, 2], [0, 0]) * qt.basis([2, 2], [0, 0]).dag()
                    + qt.basis([2, 2], [1, 1]) * qt.basis([2, 2], [1, 0]).dag()
                    + qt.basis([2, 2], [1, 0]) * qt.basis([2, 2], [1, 1]).dag()
                    + qt.basis([2, 2], [0, 1]) * qt.basis([2, 2], [0, 1]).dag()
                )
            elif i != target:
                ops.append(qt.qeye(2))

        return qt.tensor(ops)

    def measure_qubit(self, state: qt.Qobj, qubit: int) -> Tuple[int, qt.Qobj]:
        """Perform measurement on specified qubit"""
        # Create measurement operator
        meas_ops = [qt.qeye(2)] * self.num_qubits
        P0 = qt.projection(2, 0, 0)
        P1 = qt.projection(2, 1, 1)
        meas_ops[qubit] = P0
        M0 = qt.tensor(meas_ops)
        meas_ops[qubit] = P1
        M1 = qt.tensor(meas_ops)

        # Calculate probabilities and normalize
        p0 = float(abs((M0 * state).norm()) ** 2)
        p1 = float(abs((M1 * state).norm()) ** 2)
        total_p = p0 + p1
        p0, p1 = p0 / total_p, p1 / total_p

        # Random measurement outcome
        result = np.random.choice([0, 1], p=[p0, p1])

        # Project state
        if result == 0:
            new_state = M0 * state / np.sqrt(p0)
        else:
            new_state = M1 * state / np.sqrt(p1)

        return result, new_state

    def run(self, qasm_str: str, shots: int) -> np.array:
        """Translate QASM to QuTiP and return measurements"""
        circuit = self.parse_qasm(qasm_str)
        print(f"run: {circuit=}")

        # Initialise measurements
        measurements = np.zeros((self.num_cregs, shots))

        for s in range(shots):
            # Initialize state to |0...0>
            psi = qt.basis([2] * self.num_qubits)

            # Apply gates and measurements
            for operation in circuit:
                if operation[0] == "measure":
                    _, qubit, reg, bit = operation
                    result, psi = self.measure_qubit(psi, qubit)
                    measurements[bit][s] = result
                elif operation[0] in ["rx", "ry", "rz"]:
                    gate, theta, qubit = operation
                    U = self.apply_single_qubit_gate(gate, qubit, theta)
                    psi = U * psi
                elif operation[0] == "cx":
                    _, control, target = operation
                    U = self.apply_cnot(control, target)
                    psi = U * psi
                else:
                    gate, target = operation
                    U = self.apply_single_qubit_gate(gate, target)
                    psi = U * psi

        return measurements
