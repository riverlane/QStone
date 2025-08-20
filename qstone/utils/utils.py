"""General utilities. Used across the jobs"""

import json
import os
import random
import re
import time
from enum import Enum
from functools import wraps
from typing import Callable, Dict, Optional

import jsonschema
import pandas as pd
import pandera.pandas as pa

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


def validate_computation_weights(config: Dict):
    users = config["users"]  #
    for user in users:
        weights_sum = sum(user["computations"].values())
        if abs(weights_sum - 1.0) > 1e-6:  # Using epsilon for float comparison
            raise ValueError(
                f"Sum of computation weights for user {user['user']} is {weights_sum}, not 1.0"
            )


def parse_json(config: str) -> Dict:
    """
    Parses the JSON file, validates it against the schema and returns a dictionary
    representation
    """
    with open(config, "r", encoding="UTF-8") as f:
        config_dict = json.loads(f.read())
    jsonschema.validate(config_dict, FULL_SCHEMA)
    validate_computation_weights(config_dict)
    return config_dict


class QpuConfiguration:
    """Defines the configuration of a QPU (Quantum Processing Unit)"""

    def __init__(self) -> None:
        """Set Qpu Configuration defaults"""
        self.qpu_ip_address = "0"
        self.qpu_port = "0"

    def load_configuration(self, config: dict) -> None:
        """Loads QPU configuration data"""
        self.qpu_ip_address = config["connectivity"]["qpu"]["ip_address"]
        self.qpu_port = config["connectivity"]["qpu"]["port"]

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
    # Extract number classical registers
    creg_defs = re.findall(r"creg [a-zA-Z]\w*\[\d+\]", qasm)
    num_cregs = 0
    for c in creg_defs:
        num_cregs += int(re.findall(r"\d+", c)[0])

    # Extract the mapping between quantum and classical registers
    mapping = []
    qreg_meas = re.findall(r"[a-zA-Z]\w*\[\d+\] -> ", qasm)
    for qreg in qreg_meas:
        trimmed = qreg[len("q[")]
        mapping.append(int(re.findall(r"\d+", trimmed)[0]))

    # Generate a random readout per shot
    measurements = []
    counts: dict = {}
    for _ in range(repetitions):
        meas = list(list(random.randint(0, 1) for _ in range(num_cregs)))
        key = "".join(str(bit) for bit in meas)
        measurements.append(meas)
        if key not in counts.keys():
            counts[key] = 1
        else:
            counts[key] += 1

    return {
        "mapping": mapping,
        "measurements": measurements,
        "counts": counts,
        "mode": "random source",
    }


def _get_job_id():
    """Returns the job id from the tool"""
    return os.environ["JOB_ID"]


def _get_content(
    times: tuple[int, int],
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
    content["start"] = times[0]  # type: ignore[assignment]
    content["end"] = times[1]  # type: ignore[assignment]
    content["success"] = success  # type: ignore[assignment]
    return content


def _write_trace(
    profile_path: str,
    times: tuple[int, int],
    computation_type: str,
    computation_step: ComputationStep,
    label: str,
    success: bool,
):
    """Handler for trace writing"""
    trace_content = _get_content(
        times, computation_type, computation_step, label, success
    )
    with open(profile_path, "w", encoding="utf-8") as fid:
        json.dump(trace_content, fid, ensure_ascii=False, indent=4)


def trace(
    computation_type: str,
    computation_step: ComputationStep,
    label: Optional[str] = None,
    logging_level: Optional[int] = 2,
):
    """General tracing of the function. Wrapper"""

    def wrapper(func: Callable):
        @wraps(func)
        def wrapper_func(*args, **kwargs):
            logging_level_met = logging_level >= int(
                os.environ.get("APP_LOGGING_LEVEL", "0")
            )
            start = time.perf_counter_ns()
            profile_name = "_".join(
                filter(
                    None,
                    (
                        "job",
                        _get_job_id(),
                        computation_step.value,
                        computation_type,
                        label,
                        str(start),
                    ),
                )
            )
            profile_path = os.path.join(
                os.environ["PROFILE_PATH"], f"{profile_name}.json"
            )
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:  # pylint: disable=broad-except
                result = None
                success = False
                raise e
            finally:
                end = time.perf_counter_ns()
                if logging_level_met:
                    _write_trace(
                        profile_path,
                        (start, end),
                        computation_type,
                        computation_step,
                        label,
                        success,
                    )
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
