"""QPU Computation registry"""

import importlib
import os

from qstone.apps.PyMatching import PyMatching
from qstone.apps.QBC import QBC
from qstone.apps.RB import RB
from qstone.apps.VQE import VQE
from qstone.connectors import connector

# Mapping computation name to its class
_computation_registry = {
    "VQE": VQE,
    "RB": RB,
    "PyMatching": PyMatching,
    "QBC": QBC,
}

ENV_VARS = {
    "CONNECTIVITY_QPU_IP_ADDRESS": os.environ.get(
        "CONNECTIVITY_QPU_IP_ADDRESS", "127.0.0.1"
    ),
    "CONNECTIVITY_QPU_PORT": int(os.environ.get("CONNECTIVITY_QPU_PORT", "0")),
    "CONNECTIVITY_COMPILER_IP_ADDRESS": os.environ.get(
        "CONNECTIVITY_COMPILER_IP_ADDRESS", "127.0.0.1"
    ),
    "CONNECTIVITY_COMPILER_PORT": int(
        os.environ.get("CONNECTIVITY_COMPILER_PORT", "0")
    ),
    "CONNECTIVITY_MODE": connector.ConnectorType[
        os.environ.get("CONNECTIVITY_MODE", "NO_LINK")
    ],
    "QPU_MODE": os.environ.get("QPU_MODE", "RANDOM"),
    "CONNECTIVITY_TARGET": os.environ.get("CONNECTIVITY_TARGET", ""),
    "LOCKFILE": (
        os.environ.get("LOCK_FILE", "qstone.lock")
        if os.environ.get("SCHEDULING_MODE", "NONE") == "LOCK"
        else None
    ),
    "OUTPUT_PATH": os.environ.get("OUTPUT_PATH", ""),
    "JOB_ID": os.environ.get("JOB_ID", 0),
    "NUM_QUBITS": int(os.environ.get("NUM_QUBITS", "0")),
}


def get_computation_src(src: str):
    """Extracts the computation src either from the standard set or from the user"""
    if src in _computation_registry:
        computation_src = _computation_registry[src]  # type: ignore [abstract]
    else:
        try:
            src_module, src_class = src.rsplit(".", 1)
            computation_src = getattr(importlib.import_module(src_module), src_class)
        except NameError as exc:
            raise NameError(
                f"{src} app not found in standard list or as a folder"
            ) from exc
    return computation_src
