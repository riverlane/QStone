"""Wrapper for QPU node"""

""" Connection abstraction for nodes."""

from abc import ABC, abstractmethod

""" Remote node is QStone independent """


class QpuConfiguration:
    """Defines the configuration of a QPU (Quantum Processing Unit)"""

    def __init__(self) -> None:
        """Set Qpu Configuration defaults"""
        self._num_required_qubits = 0
        self.qpu_ip_address = "0"
        self.qpu_port = "0"

    @property
    def num_required_qubits(self) -> int:
        """Required qubits getter"""
        return self._num_required_qubits

    @num_required_qubits.setter
    def num_required_qubits(self, value):
        """Required qubits setter"""
        self._num_required_qubits = int(value)

    def load_configuration(self, config: dict) -> None:
        """Loads QPU configuration data"""
        if "num_required_qubits" in config:
            self.num_required_qubits = int(config["num_required_qubits"])
        else:
            self.num_required_qubits = int(config["_num_required_qubits"])
        self.qpu_ip_address = config["qpu_ip_address"]
        self.qpu_port = config["qpu_port"]

    def write_configuraiton(self, output_path: str) -> None:
        """Writes QPU configuration as json

        Args:
            output_path: File path to write configuration to
        """
        config = {}
        config["num_required_qubits"] = self.num_required_qubits
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(config, file)

    def _compatible(self, qpu_config: "QpuConfiguration") -> bool:
        """Checks if given QPU configuration is a subset of this instance"""
        if self.num_required_qubits < qpu_config.num_required_qubits:
            return False
        return True

    def is_compatible(
        self, qpu_config: "QpuConfiguration", superset: bool = False
    ) -> bool:
        """Checks if given QPU configuration is compatible with this instance

        Args:
            qpu_config : Target qpu configuration to compare with this instance
            superset: Whether to check the target qpu config is a subset or superset
            of this instance
        Returns:
            Whether resources of target QPU is compatible with this isntance
        """
        if superset:
            return qpu_config.is_compatible(self)
        return self._compatible(qpu_config)


class QPU(ABC):
    """
    Abstract class to represent QPU compute node exectuon wrapper

    Args:
        qpu_cfg: QpuConfiguration object defining qpu node configuration.
    """

    def __init__(self, qpu_cfg: QpuConfiguration) -> None:
        self.qpu_cfg = qpu_cfg

    @abstractmethod
    def exec(self, qasm: str, shots: int) -> dict:
        """
        Execute the quantum circuit

        Args:
            qasm: represnetation of quantum circuit in openqasm format.
            shots: number of shots to repeat circuit.
        """
