"""Quantum executor over a HTTP channel"""

import json
import os
import secrets
import sys
from time import sleep

import requests

from qstone.connectors import connection
from qstone.utils.utils import ComputationStep, QpuConfiguration, trace


class HttpConnection(connection.Connection):
    """Connection running jobs over Http"""

    def __init__(self):
        """Creates the empty response"""
        self.response = None
        self.http_timeout = int(os.environ.get("TIMEOUTS_HTTP", 10))
        self.lock_timeout = int(os.environ.get("TIMEOUTS_LOCK", 200))

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.PRE,
    )
    def preprocess(self, qasm_ptr: str) -> str:
        """Preprocess the data."""
        # Currently passthrough.
        with open(qasm_ptr, "r", encoding="utf-8") as fid:
            return fid.read()

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.POST,
    )
    def postprocess(self, message: str) -> str:
        """Postprocess the data"""
        # If the message is None we return an empty string.
        # Please note. In this model it is responsability of the gateway machine to
        # return the data in the correct format as defined in assumptions.md
        return json.loads(message) if message else ""

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.RUN,
        label="_request_and_process",
    )
    def _request_and_process(self, qasm_ptr: str, reps: int, hostpath: str):
        pkt_id = secrets.randbelow(2**31)
        circuit = self.preprocess(qasm_ptr)
        payload = {"circuit": circuit, "pkt_id": pkt_id, "reps": reps}
        headers: dict = {}
        r = requests.post(
            f"{hostpath}/execute", timeout=10, headers=headers, json=payload
        )
        success = r.status_code == 200
        if success:
            r = requests.get(
                f"{hostpath}/results",
                timeout=self.http_timeout,
                json={"pkt_id": pkt_id},
            )
            self.response = r.text
            success = r.status_code == 200
        if not success:
            sys.stderr.write("QSTONE::ERR - Request failed")
        return success

    # mypy: disable-error-code="attr-defined"
    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.RUN,
    )
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
        qpu_hostpath = f"{qpu_host}:{qpu_port}" if qpu_port else qpu_host
        # Prepending the HTTP specifier if not provided.
        qpu_hostpath = (
            qpu_hostpath
            if qpu_hostpath.startswith("http://")
            else f"http://{qpu_hostpath}"
        )

        # Active wait on lock
        if lockfile is not None:
            owned = False
            lock = connection.FileLock(lockfile)
            for _ in range(10 * self.lock_timeout):
                if lock.acquire_lock():
                    owned = True
                    break
                sleep(0.1)
            if not owned:
                sys.stderr.write("QSTONE::ERR - timeout waiting for lock")
                return {}

        self._request_and_process(qasm_ptr, reps, qpu_hostpath)

        # releasing lock takes care of None case as well.
        if lockfile is not None:
            lock.release_lock()
        return self.postprocess(self.response)

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.QUERY,
    )
    def query_qpu_config(self, host: str, server_port: int) -> QpuConfiguration:
        """Query the Qpu configuraiton of the target"""
        hostpath = f"{host}"
        if server_port:
            hostpath += f":{server_port}"
        response = requests.get(f"{hostpath}/qpu/config", timeout=10)
        qpu_config = QpuConfiguration()
        if response.ok:
            qpu_config.load_configuration(json.loads(response.text))
        return qpu_config
