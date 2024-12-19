""" Quantum executor for Rigetti backend """

import calendar
import time

import numpy
import waiting
from pyquil import Program, get_qc

from qstone.connectors import connection
from qstone.utils.utils import ComputationStep, QpuConfiguration, trace


class RigettiConnection(connection.Connection):
    """Connection running jobs to Rigetti backend"""

    def __init__(self):
        """Creates the empty response"""
        self.response = None
        self.qc = None
        self.result = None
        self.mode = None
        self.origin = None

    def _get_qc(self, hostpath: str):
        self.mode = "simulated" if "qvm" in hostpath else "real"
        self.origin = hostpath
        return get_qc(hostpath)

    def _run(self, program: Program):
        return self.qc.run(program)

    def _compile(self, circuit: Program, reps: int):
        return self.qc.compile(circuit.wrap_in_numshots_loop(reps))

    def _get_results(self, run):
        # "c" is the register used to store the classical value
        return run.data.result_data.to_register_map().get("c").to_ndarray()

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.PRE,
    )
    def preprocess(self, qasm_ptr: str) -> Program:
        """Preprocess the data. Transform QASM format into PyQuil"""
        with open(qasm_ptr, "r", encoding="utf-8") as fid:
            return self.qc.compiler.transpile_qasm_2(fid.read())

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.POST,
    )
    def postprocess(self, message: str) -> dict:
        """Postprocess the data"""
        # Data is returned in the format defined in assumptions.md.
        # Mapping is currently "complete" and in order.
        mapping = list(range(len(self.result[0])))
        timestamp = calendar.timegm(time.gmtime())
        origin = self.origin
        msg = {
            "mapping": mapping,
            "measurements": self.result,
            "mode": self.mode,
            "timestamp": timestamp,
            "origin": origin,
        }
        return msg

    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.QUERY,
        label="_request_and_process",
    )
    def _request_and_process(
        self, qasm_ptr: str, reps: int, hostpath: str, lockfile: str
    ):
        circuit = self.preprocess(qasm_ptr)
        self.response = None
        success = False
        lock = connection.FileLock(lockfile)
        if lock.acquire_lock():
            run = self._run(self._compile(circuit, reps))
            self.result = self._get_results(run)
            success = True
        return success

    # mypy: disable-error-code="attr-defined"
    @trace(
        computation_type="CONNECTION",
        computation_step=ComputationStep.RUN,
    )
    def run(
        self, qasm_ptr: str, reps: int, host: str, server_port: int, lockfile: str
    ) -> dict:
        """Run the connection to the server"""
        if server_port:
            hostpath = f"{host}:{server_port}"
        else:
            hostpath = host
        self.qc = self._get_qc(hostpath)
        try:
            waiting.wait(
                lambda: self._request_and_process(qasm_ptr, reps, hostpath, lockfile),
                timeout_seconds=20,
            )
        except waiting.TimeoutExpired:
            pass
        return self.postprocess(self.response)
