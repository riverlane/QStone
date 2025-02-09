import re
from typing import List, Tuple, Dict
import numpy as np
import qutip as qt

class QASMToQuTiP:
    def __init__(self):
        # Standard single-qubit gates as QuTiP operators
        self.gates = {
            'x': qt.sigmax(),
            'y': qt.sigmay(),
            'z': qt.sigmaz(),
            'h': qt.Qobj([[1, 1], [1, -1]]) / np.sqrt(2),
            's': qt.Qobj([[1, 0], [0, 1j]]),
            't': qt.Qobj([[1, 0], [0, np.exp(1j*np.pi/4)]])
        }
        self.measurements = {}  # Store measurement results
    
    def rx(self, theta: float) -> qt.Qobj:
        """Create Rx rotation gate"""
        return qt.Qobj([[np.cos(theta/2), -1j*np.sin(theta/2)],
                       [-1j*np.sin(theta/2), np.cos(theta/2)]])
    
    def ry(self, theta: float) -> qt.Qobj:
        """Create Ry rotation gate"""
        return qt.Qobj([[np.cos(theta/2), -np.sin(theta/2)],
                       [np.sin(theta/2), np.cos(theta/2)]])
    
    def rz(self, theta: float) -> qt.Qobj:
        """Create Rz rotation gate"""
        return qt.Qobj([[np.exp(-1j*theta/2), 0],
                       [0, np.exp(1j*theta/2)]])
    
    def parse_qasm(self, qasm_str: str) -> List[Tuple]:
        """Parse QASM string into list of operations"""
        circuit = []
        
        # Remove comments and empty lines
        lines = [line.split('//')[0].strip() for line in qasm_str.split('\n')]
        lines = [line for line in lines if line]
        
        for line in lines:
            if line.startswith('OPENQASM') or line.startswith('include'):
                continue
                
            if line.startswith('qreg'):
                match = re.search(r'qreg\s+\w+\[(\d+)\]', line)
                if match:
                    self.num_qubits = int(match.group(1))
                continue
                
            if line.startswith('creg'):
                match = re.search(r'creg\s+(\w+)\[(\d+)\]', line)
                if match:
                    reg_name, size = match.groups()
                    self.measurements[reg_name] = [None] * int(size)
                continue
            
            # Parse measurements
            measure_match = re.match(r'measure\s+q\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]', line)
            if measure_match:
                qubit, reg, bit = measure_match.groups()
                circuit.append(('measure', int(qubit), reg, int(bit)))
                continue
            
            # Parse rotation gates
            rot_match = re.match(r'(rx|ry|rz)\(([^)]+)\)\s+q\[(\d+)\]', line)
            if rot_match:
                gate, angle, qubit = rot_match.groups()
                # Convert angle to float (handle pi notation)
                angle = float(eval(angle.replace('pi', 'np.pi')))
                circuit.append((gate, angle, int(qubit)))
                continue
            
            # Parse standard gates
            gate_match = re.match(r'([a-z]+)\s+(q\[\d+\])', line)
            if gate_match:
                gate, qubit = gate_match.groups()
                qubit_idx = int(re.search(r'\[(\d+)\]', qubit).group(1))
                circuit.append((gate, qubit_idx))
                continue
                
            # Parse CNOT gates
            cx_match = re.match(r'cx\s+q\[(\d+)\],\s*q\[(\d+)\]', line)
            if cx_match:
                control, target = map(int, cx_match.groups())
                circuit.append(('cx', control, target))
                
        return circuit

    def apply_single_qubit_gate(self, gate: str, qubit: int, theta: float = None) -> qt.Qobj:
        """Create QuTiP operator for single-qubit gate"""
        ops = [qt.qeye(2)] * self.num_qubits
        
        if gate in ['rx', 'ry', 'rz']:
            if gate == 'rx':
                ops[qubit] = self.rx(theta)
            elif gate == 'ry':
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
                ops.append(qt.basis([2, 2], [0, 0]) * qt.basis([2, 2], [0, 0]).dag() +
                         qt.basis([2, 2], [1, 1]) * qt.basis([2, 2], [1, 0]).dag() +
                         qt.basis([2, 2], [1, 0]) * qt.basis([2, 2], [1, 1]).dag() +
                         qt.basis([2, 2], [0, 1]) * qt.basis([2, 2], [0, 1]).dag())
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
        
        # Calculate probabilities
        p0 = abs((M0 * state).norm())
        p1 = abs((M1 * state).norm())
        
        # Random measurement outcome
        result = np.random.choice([0, 1], p=[p0, p1])
        
        # Project state
        if result == 0:
            new_state = M0 * state / np.sqrt(p0)
        else:
            new_state = M1 * state / np.sqrt(p1)
            
        return result, new_state
    
    def translate(self, qasm_str: str) -> Tuple[qt.Qobj, Dict]:
        """Translate QASM to QuTiP and return final state and measurements"""
        circuit = self.parse_qasm(qasm_str)
        
        # Initialize state to |0...0>
        psi = qt.basis([2] * self.num_qubits)
        
        # Apply gates and measurements
        for operation in circuit:
            if operation[0] == 'measure':
                _, qubit, reg, bit = operation
                result, psi = self.measure_qubit(psi, qubit)
                self.measurements[reg][bit] = result
            elif operation[0] in ['rx', 'ry', 'rz']:
                gate, theta, qubit = operation
                U = self.apply_single_qubit_gate(gate, qubit, theta)
                psi = U * psi
            elif operation[0] == 'cx':
                _, control, target = operation
                U = self.apply_cnot(control, target)
                psi = U * psi
            else:
                gate, target = operation
                U = self.apply_single_qubit_gate(gate, target)
                psi = U * psi
            
        return psi, self.measurements

# Example usage
if __name__ == "__main__":
    # Example QASM string with rotations and measurement
    qasm_str = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    rx(pi/4) q[0];
    ry(pi/2) q[1];
    cx q[0],q[1];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    """
    
    # Create translator and run
    translator = QASMToQuTiP()
    final_state, measurements = translator.translate(qasm_str)
    
    print("Final state:")
    print(final_state)
    print("\nMeasurement results:")
    print(measurements)
