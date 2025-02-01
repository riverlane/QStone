"""RB computations steps."""

import os

import numpy as np
import pygsti
from pandera import Check, Column, DataFrameSchema
from pygsti.processors import CliffordCompilationRules as CCR
from pygsti.processors import QubitProcessorSpec as QPS

from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace


class RB(Computation):
    """
    Type 1 computation class.
    """

    COMPUTATION_NAME = "RB"
    CFG_STRING = """
    {
      "cfg":
      {
         "num_required_qubits" : 2,
         "repetitions": 2
      }
    } 
    """
    SCHEMA = DataFrameSchema(
        {
            "repetitions": Column(int, Check(lambda s: s >= 0)),
        }
    )

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        # Hints - do not remove
        self.repetitions: int
        self.num_shots = int(os.environ.get("NUM_SHOTS", self.repetitions))

    def _get_configuration(self):
        """Returns standard configuration for the job."""
        n_qubits = int(os.environ["NUM_QUBITS"])
        if n_qubits > 2:
            n_qubits = 2
            print("Maximum number of supported qubits is 2. Trimming down request")
        n_active_qubits = 1
        depths = [1, 4, 8, 16]
        reps = 10
        qubit_labels = [f"Q{s}" for s in range(n_qubits)]
        gate_names = ["Gxpi2", "Gxmpi2", "Gypi2", "Gympi2", "Gcphase"]
        availability = {
            "Gcphase": [
                ("Q0", "Q1"),
                ("Q1", "Q0"),
            ]
        }
        pspec = QPS(
            n_qubits, gate_names, availability=availability, qubit_labels=qubit_labels
        )
        compilations = {
            "absolute": CCR.create_standard(
                pspec, "absolute", ("paulis", "1Qcliffords"), verbosity=0
            ),
            "paulieq": CCR.create_standard(
                pspec, "paulieq", ("1Qcliffords", "allcnots"), verbosity=0
            ),
        }
        # Only using Q0 for now
        active_qubit_labels = ["Q0"]
        design = pygsti.protocols.CliffordRBDesign(
            pspec, compilations, depths, reps, active_qubit_labels
        )
        print(f"Generated benchmarking routing with {n_qubits} qubits")
        return (design, pspec, active_qubit_labels, n_active_qubits)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """
        Generates the circuits required to extract the randomised benchmarking
        circuits.
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"
        design, _, active_qubit_labels, n_active_qubits = self._get_configuration()
        # Translation to OpenQASM
        circuit_list_nested = design.all_circuits_needing_data
        qubit_indices = {label: i for i, label in enumerate(active_qubit_labels)}
        qasms = [
            c.convert_to_openqasm(
                num_qubits=n_active_qubits,
                standard_gates_version="x-sx-rz",
                qubit_conversion=qubit_indices,
            )
            for c in circuit_list_nested
        ]
        # Flatten out fully. We might want to consider keeping the N steps separate
        exp = list(np.concatenate(design.idealout_lists).flat)
        # Generate a .npz file that contains the configuration
        np.savez(run_file, qasms=qasms, exp=exp, allow_pickle=True)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.RUN)
    def run(self, datapath: str, connection: connector.Connector):
        """Runs the Quantum circuit N times

        Args:
            datapath: path location to write circuit
            connection: connector object to run circuit
            shots: number of shots to be executed
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"
        # Find number of circuits
        results = []
        # load configuration (and qasm files)
        vals = np.load(run_file)
        i = 0
        for circuit in vals["qasms"]:
            path = os.path.join(
                os.path.dirname(run_file), f"RB_{os.environ['JOB_ID']}_{str(i)}.qasm"
            )
            with open(path, "w", encoding="utf-8") as fid:
                fid.write(circuit)
            i = i + 1
            results.append(connection.run(qasm=path, reps=self.num_shots))
        store = {"qasms": vals["qasms"], "exp": vals["exp"], "res": results}
        np.savez(run_file, **store, allow_pickle=True)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Runs the processing of the randomised benchmarking using the data provided by
        datapath
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"
        report_file = f"{datapath}/RB_report_{os.environ['JOB_ID']}.txt"
        vals = np.load(run_file, allow_pickle=True)
        exp = vals["exp"]
        res = vals["res"]
        success_counts = np.count_nonzero(exp == res)
        with open(report_file, "w", encoding="utf-8") as fid:
            fid.write(f"success_counts: {success_counts}")
