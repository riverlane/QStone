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

import pandas as pd
import pandera as pa


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

JOB_SCHEMA = pa.DataFrameSchema(
    {
        "type": pa.Column(str),
        "qubit_min": pa.Column(int),
        "qubit_max": pa.Column(int),
        "num_shots_min": pa.Column(int),
        "num_shots_max": pa.Column(int),
        "path": pa.Column(str, nullable=True, required=False),
        "walltime": pa.Column(int, nullable=True, required=False),
        "nthreads": pa.Column(int, nullable=True, required=False),
    }
)


USER_SCHEMA = pa.DataFrameSchema(
    {
        "user": pa.Column(str),
        "weight": pa.Column(checks=pa.Check.in_range(0, 1.0)),
        "computations": pa.Column(Dict),
    }
)

TIMEOUT_SCHEMA = pa.DataFrameSchema(
    {
        "http": pa.Column(int),
        "lock": pa.Column(int),
    }
)


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


def load_users(config_path, schema):
    """Loading a json file and checking it against the schema"""
    with open(config_path, "r", encoding="utf8") as _file:
        config = json.load(_file)
    return schema(pd.DataFrame.from_dict(config["users"], orient="columns"))


def load_jobs(config_path, schema):
    """Loading a json file and checking it against the schema"""
    with open(config_path, "r", encoding="utf8") as _file:
        config = json.load(_file)
    return schema(pd.DataFrame.from_dict(config["jobs"], orient="columns"))


def _get_value(config, env_var):
    """Get dictionary values represented in root based hierarchical representation"""
    tokens = env_var.split(".")
    for token in tokens:
        config = config.get(token, {})
    return config if config else "NONE"


def get_config_environ_vars(config_path: str) -> dict:
    """Gets the config type from the input configuration

    Parses the config to extract the connector type and returns the associated enum value

    Args:
        config_path: path to config file

    Returns:
        ConnectorType enum value
    """
    with open(config_path, "r", encoding="utf8") as _file:
        config = json.load(_file)
    environ_vars = {
        env_var: _get_value(config, env_var) for env_var in CFG_ENVIRONMENT_VARIABLES
    }
    return environ_vars


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
