""" General utilities. Used across the jobs """

import json
import os
import random
import re
import time
from collections import defaultdict
from enum import Enum
from functools import wraps
from typing import Callable, Dict, Optional

import jsonschema
import pandas as pd
import pandera as pa

from .config_schema import FULL_SCHEMA


class JobReturnCode(Enum):
    """Type of exit code of job run"""

    JOB_COMPLETED = 0
    INSUFFICIENT_QPU_RESOURCES = 1
    PRE_STEP_INCOMPLETE = 2
    RUN_STEP_INCOMPLETE = 3
    POST_STEP_INCOMPLETE = 4


class ComputationStep(Enum):
    """Step of computation for profiling"""

    PRE = "PRE"
    RUN = "RUN"
    POST = "POST"
    QUERY = "QUERY"


CFG_ENVIRONMENT_VARIABLES = {
    "project_name",
    "connector",
    "qpu_ip_address",
    "qpu_port",
    "qpu_management",
    "lock_file",
    "timeouts.http",
    "timeouts.lock",
}


def parse_json(config: str) -> Dict:
    """Parses the JSON file, validates it against the schema and returns a dictionary representation"""
    with open(config) as f:
        config_dict = json.loads(f.read())
    jsonschema.validate(config_dict, FULL_SCHEMA)
    return config_dict


class QpuConfiguration:
    """Defines the configuration of a QPU (Quantum Processing Unit)"""

    def __init__(self) -> None:
        """Set Qpu Configuration defaults"""
        self.qpu_ip_address = "0"
        self.qpu_port = "0"

    def load_configuration(self, config: dict) -> None:
        """Loads QPU configuration data"""
        self.qpu_ip_address = config["qpu_ip_address"]
        self.qpu_port = config["qpu_port"]

    def write_configuration(self, output_path: str) -> None:
        """Writes QPU configuration as json

        Args:
            output_path: File path to write configuration to
        """
        config = {"QPU_ADDRESS": self.qpu_ip_address, "QPU_PORT": self.qpu_port}
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(config, file)


def qasm_circuit_random_sample(qasm: str, repetitions: int) -> Dict:
    """Mocks simulation of qasm circuit by giving random readouts for classical registers

    Args:
        qasm: string representation of qasm circuit
        repetitions: number of readouts to simulate
    Returns frequency of each classical bit string sampled
    """
    # Extract size of classical registers
    creg_defs = re.findall(r"creg [a-zA-Z]\w*\[\d+\]", qasm)

    cregs = {}

    for creg in creg_defs:
        trimmed = creg[len("creg ") :]
        regname = re.findall(r"\w*", trimmed)[0]
        regsize = re.findall(r"\d+", trimmed)[0]
        cregs[regname] = int(regsize)

    # For each classical register generate a random readout
    readouts = {}
    for regname, regsize in cregs.items():
        outcomes: Dict = defaultdict(int)
        for _ in range(repetitions):
            outcome = "".join([random.choice("01") for _ in range(regsize)])
            outcomes[outcome] += 1
        readouts[regname] = outcomes
    return readouts


def _get_job_id():
    """Returns the job id from the tool"""
    return os.environ["JOB_ID"]


def _get_content(
    start_time: int,
    end_time: int,
    computation_type: str,
    computation_step: ComputationStep,
    label: Optional[str],
    success: bool,
):
    """Returns the dictionary that represents the time trace datapoint"""
    content = {}
    content["user"] = os.environ["QS_USER"]
    content["prog_id"] = os.environ["PROG_ID"]
    content["job_id"] = _get_job_id()
    content["job_type"] = computation_type
    content["job_step"] = computation_step.value
    content["label"] = label  # type: ignore[assignment]
    content["start"] = start_time  # type: ignore[assignment]
    content["end"] = end_time  # type: ignore[assignment]
    content["success"] = success  # type: ignore[assignment]
    return content


def trace(
    computation_type: str,
    computation_step: ComputationStep,
    label: Optional[str] = None,
):
    """General tracing of the function. Wrapper"""

    def wrapper(func: Callable):
        @wraps(func)
        def wrapper_func(*args, **kwargs):

            success = True
            start = time.perf_counter_ns()
            try:
                result = func(*args, **kwargs)
            except Exception:  # pylint: disable=broad-except
                result = None
                success = False
            end = time.perf_counter_ns()
            trace_content = _get_content(
                start, end, computation_type, computation_step, label, success
            )
            profile_name = "_".join(
                filter(
                    None,
                    (
                        "job",
                        _get_job_id(),
                        computation_step.value,
                        computation_type,
                        label,
                    ),
                )
            )
            profile_path = os.path.join(
                os.environ["PROFILE_PATH"], f"{profile_name}.json"
            )
            with open(profile_path, "w", encoding="utf-8") as fid:
                json.dump(trace_content, fid, ensure_ascii=False, indent=4)
            return result

        return wrapper_func

    return wrapper


def load_json_profile(trace_info: str, schema: pa.DataFrameSchema) -> pd.DataFrame:
    """Loads function json profile and checks it against the schema

    Args:
        trace_info: File location of function traced information
        schema: Validator schema

    Returns pandas dataframe containing profile information
    """
    with open(trace_info, "r", encoding="utf-8") as f:
        df = pd.json_normalize(json.load(f))
    schema.validate(df)
    return df
