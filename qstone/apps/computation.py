"""QPU computation class and configuration dataclass"""

import base64
import json
import os
import pickle
from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd
from pandera import DataFrameSchema

from qstone.connectors import connector
from qstone.utils.utils import QpuConfiguration


def byte_to_dict(s: str) -> Dict:
    """converts a json formatted string into a dictionary"""
    if not s:
        return {}
    decoded = base64.b64decode(s.encode("utf-8"))
    return pickle.loads(decoded)


class Computation(ABC):
    """
    Abstract class for a QPU computation.
    To be ovverriden  by implemented jobs.

    Args:
        cfg: Computation configuration dictionary. Key value pairs describing
        the script data.
    """

    COMPUTATION_NAME: str
    CFG_PATH: Optional[str] = None
    CFG_STRING: Optional[str] = None
    SCHEMA: DataFrameSchema
    BASEPATH: str = os.path.join(os.path.dirname(__file__), "..")

    def __init__(self, cfg: Dict):
        self._cfg = cfg
        for key, val in cfg.items():
            setattr(self, key, val)
        self._qpu_cfg = QpuConfiguration()
        self._app_args = byte_to_dict(os.environ.get("APP_ARGS", ""))
        self._logging_level = os.environ.get("LOGGING_LEVEL", "")

    @classmethod
    def from_json(cls, path: Optional[str] = None):
        """Factory method for creating computation via JSON configuration.

        Args:
            path: Path to computation configuration file
        """
        if cls.CFG_STRING is None:
            if path is None:
                path = os.path.join(cls.BASEPATH, cls.CFG_PATH)  # type:ignore
            with open(path, encoding="utf-8") as fo:
                json_obj = json.load(fo)
        else:
            json_obj = json.loads(cls.CFG_STRING)
        cfg = json_obj["cfg"]
        df = pd.json_normalize(cfg)
        cls.SCHEMA.validate(df)
        return cls(cfg)

    def dump_cfg(self) -> str:
        """
        Serializes computation script information into JSON string.

        Returns json string representation of computation configuration.
        """
        return json.dumps(self._cfg)

    @property
    def qpu_cfg(self):
        """qpu_cfg getter"""
        return self._qpu_cfg

    @abstractmethod
    def pre(self, datapath: str) -> None:
        """QPU computation preprocessing step"""
        raise NotImplementedError

    @abstractmethod
    def run(self, datapath: str, connection: connector.Connector):
        """QPU computation circuit run step"""
        raise NotImplementedError

    @abstractmethod
    def post(self, datapath):
        """QPU computation postprocessing step"""
        raise NotImplementedError
