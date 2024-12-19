"""Mock for QPU model"""

from typing import Any
from _qpu import QPU, QpuConfiguration


class Mock_QPU(QPU):
    """Mock for QPU model. Class."""

    def __init__(self):
        qpu_cfg = QpuConfiguration()
        qpu_cfg.num_required_qubits = 4
        super().__init__(qpu_cfg)

    def _qasm_to_internal(self, qasm: str) -> Any:
        """This function should transpile from QASM to native (if required)"""
        print(f"Passed qasm string: {qasm}")
        return "NOP"

    def _run(self, program: Any, shots: int, blocking: bool):
        """This function should run the programme"""
        print(
            f"Loading {program} to run {shots} shots with blocking mode: {blocking}..."
        )

    def _get_results(self):
        """This function should run the programme and return the results in line with assumptions.md"""
        outcomes = [[0, 0, 0]] * 100

        return outcomes

    def exec(self, qasm: str, shots: int) -> dict:
        """Model running time of circuit"""
        transpiled = self._qasm_to_internal(qasm)
        self._run(transpiled, shots, blocking=True)
        return self._get_results()
