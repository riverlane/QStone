"""Connection abstraction for nodes."""

import os
from abc import ABC, abstractmethod
from pathlib import Path


class FileLock:
    """Implementation of the file locking system."""

    def __init__(self, lockfile: str):
        """Lock creation"""
        self._lockfile = lockfile

    def acquire_lock(self) -> bool:
        """Tries to acquire the lock. Atomic way"""
        if self._lockfile is None:
            locked = True
        else:
            try:

                # Atomic operation
                Path(self._lockfile).touch(exist_ok=False)
                locked = True
            except FileExistsError:
                locked = False
        return locked

    def release_lock(self):
        """Releases the lock."""
        if self._lockfile:
            os.remove(self._lockfile)


class Connection(ABC):
    """Abstract class to represent connection between nodes"""

    @abstractmethod
    def preprocess(self, qasm_ptr: str) -> str:
        """Preprocess the data."""

    @abstractmethod
    def postprocess(self, message: str) -> dict:
        """Postprocess the data"""

    @abstractmethod
    def run(
        self,
        qasm_ptr: str,
        reps: int,
        mode: str,
        qpu_host: str,
        qpu_port: int,
        compiler_host: str,
        compiler_port: int,
        target: str,
        lockfile: str,
    ) -> dict:
        """Run the connection to the server"""
