"""Simulation abstract class"""

from abc import ABC, abstractmethod


class Simulation(ABC):
    """Simulation abstract class"""

    @abstractmethod
    def run(self, qasm: str) -> []:
        """Runs a quantum circuit"""
        raise NotImplementedError
