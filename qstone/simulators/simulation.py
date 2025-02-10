from abc import ABC, abstractmethod


class Simulation(ABC):

    @abstractmethod
    def run(self, qasm: str) -> []:
        """Runs a quantum circuit"""
        raise NotImplementedError
