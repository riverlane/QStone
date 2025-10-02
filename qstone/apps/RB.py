"""RB computations steps."""

import ast
import base64
import json
import os
import pickle
from typing import Any

import numpy as np
import pygsti
from pandera import Check, Column, DataFrameSchema, Object
from pygsti.processors import CliffordCompilationRules as CCR
from pygsti.processors import QubitProcessorSpec as QPS

from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace


def _to_ob(string):
    return pickle.loads(base64.b64decode(string.encode("utf-8")))


class RB(Computation):
    """
    Randomized Benchmarking (RB) computation class.
    """

    COMPUTATION_NAME = "RB"
    CFG_STRING = """
    {
      "cfg":
      {
         "num_required_qubits" : 4,
         "benchmarks" : [[0]],
         "depths" : [0,2,4,8],
         "reps" : 10,
         "shots": 8
      }
    } 
    """
    SCHEMA = DataFrameSchema(
        {
            "benchmarks": Column(
                Object,
                Check(
                    lambda s: s.apply(
                        lambda x: isinstance(x, list)
                        and all(
                            isinstance(i, list) and all(isinstance(j, int) for j in i)
                            for i in x
                        )
                    )
                ),
            ),
            "depths": Column(
                Object,
                Check(
                    lambda s: s.apply(
                        lambda x: isinstance(x, list)
                        and all(isinstance(i, int) for i in x)
                    )
                ),
            ),
            "reps": Column(int, Check(lambda s: s >= 0)),
            "shots": Column(int, Check(lambda s: s >= 0)),
        }
    )

    def __init__(self, cfg: dict):
        super().__init__(cfg)

        self.num_required_qubits = int(
            os.environ.get("NUM_QUBITS", cfg.get("num_required_qubits", 4))
        )
        self.shots = int(os.environ.get("NUM_SHOTS", str(cfg.get("shots", 8))))
        app_args: dict = {}
        env_app_args = os.environ.get("APP_ARGS", "")
        if env_app_args != "":
            loaded = _to_ob(env_app_args)
            if isinstance(loaded, dict):
                app_args = loaded
        else:
            pass
        if "benchmarks" in app_args.keys():
            self.benchmarks = app_args["benchmarks"]
        if "depths" in app_args.keys():
            self.depths = app_args["depths"]
        if "reps" in app_args.keys():
            self.reps = app_args["reps"]

    @trace(
        computation_type="RB",
        computation_step=ComputationStep.PRE,
        label="BENCHMARK_VALIDATION",
        logging_level=4,
    )
    def _get_allowed_benchmarks(self):
        """
        Takes the lists of requested randomized benchmarks and returns a list
        with those that can be run simultaneously in a quantum circuit
        """

        benchs = []

        for bench in self.benchmarks:

            if (
                bench not in benchs
                and all(x not in [q for ben in benchs for q in ben] for x in bench)
                and all(x < self.num_required_qubits for x in bench)
            ):
                benchs.append(bench)

        self.benchmarks = benchs

    @trace(
        computation_type="RB",
        computation_step=ComputationStep.PRE,
        label="BENCHMARK_CONFIGURATION",
        logging_level=4,
    )
    def _get_configuration(self, bench):
        """
        Returns standard configuration for the RB
        """
        n_qubits = len(bench)
        qubit_labels = list(f"Q{q}" for q in bench)
        gate_names = ["Gxpi2", "Gxmpi2", "Gypi2", "Gympi2"]
        if n_qubits == 2:
            gate_names += ["Gcphase"]
            availability = {"Gcphase": [tuple(qubit_labels), tuple(qubit_labels[::-1])]}
        if n_qubits == 1:
            pspec = QPS(n_qubits, gate_names, qubit_labels=qubit_labels)
        elif n_qubits == 2:
            pspec = QPS(
                n_qubits,
                gate_names,
                availability=availability,
                qubit_labels=qubit_labels,
            )
        else:
            raise ValueError(f"Unsupported number of qubits: {n_qubits}")
        compilations = {
            "absolute": CCR.create_standard(
                pspec, "absolute", ("paulis", "1Qcliffords"), verbosity=0
            ),
            "paulieq": CCR.create_standard(
                pspec, "paulieq", ("1Qcliffords", "allcnots"), verbosity=0
            ),
        }
        design = pygsti.protocols.MirrorRBDesign(
            pspec=pspec,
            clifford_compilations=compilations,
            depths=self.depths,
            circuit_type="clifford",
            circuits_per_depth=self.reps,
            qubit_labels=qubit_labels,
        )
        print(f"Generated benchmarking routing with {n_qubits} qubits")
        return qubit_labels, pspec, design

    @trace(
        computation_type="RB",
        computation_step=ComputationStep.PRE,
        label="QASM_GENERATION",
        logging_level=3,
    )
    def _generate_rb_qasms(self):
        self._get_allowed_benchmarks()
        bench_qasms = []
        idealouts = []

        for bench in self.benchmarks:
            # Here we get each benchmark configuration
            qubit_labels, _, design = self._get_configuration(bench)

            # Here we construct each benchmark circuits
            circuit_list_nested = design.all_circuits_needing_data
            bench_qasms.append(
                list(
                    c.convert_to_openqasm(
                        num_qubits=self.num_required_qubits,
                        standard_gates_version="x-sx-rz",
                        qubit_conversion=dict(zip(qubit_labels, bench)),
                    )
                    for c in circuit_list_nested
                )
            )
            idealouts += list(np.concatenate(design.idealout_lists).flat)

        # Here we combine the qasm files of circuits that can be run simultaneosly into one single qasm
        qasms = []
        for i in range(len(bench_qasms[0])):
            qasm = []
            for j in range(len(bench_qasms)):
                temp = list(
                    line for line in bench_qasms[j][i].splitlines() if line != ""
                )
                initial_line=0
                if j != 0: 
                    for k, line in enumerate(temp):
                        if line.startswith('creg'):
                            initial_line=k+1
                            break
                qasm += temp[initial_line:]

            qasms.append("".join("{}\n".format(line) for line in qasm))

        return qasms, idealouts

    @trace(
        computation_type=COMPUTATION_NAME,
        computation_step=ComputationStep.PRE,
        label="BENCHMARK_SET_UP",
    )
    def pre(self, datapath: str):
        """
        Generates the quantum circuits required to extract
        the survival probability of each requested RB
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"

        qasms, idealouts = self._generate_rb_qasms()

        np.savez(run_file, qasms=qasms, exp=idealouts, allow_pickle=True)

    @trace(
        computation_type=COMPUTATION_NAME,
        computation_step=ComputationStep.RUN,
        label="BENCHMARK_RUN",
    )
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
            results.append(connection.run(qasm=path, reps=self.shots))

        store = {"qasms": vals["qasms"], "exp": vals["exp"], "res": results}
        np.savez(run_file, **store, allow_pickle=True)

    @trace(
        computation_type=COMPUTATION_NAME,
        computation_step=ComputationStep.POST,
        label="SURVIVAL_ESTIMATION",
    )
    def post(self, datapath: str):
        """Runs the post-processing of the randomised benchmarking
        using the data provided by datapath
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"
        report_file = f"{datapath}/RB_report_{os.environ['JOB_ID']}.txt"
        self._get_allowed_benchmarks()
        vals = np.load(run_file, allow_pickle=True)
        if "exp" in vals:
            exp = vals["exp"]
            if exp.size == len(self.benchmarks) * len(self.depths) * self.reps:
                exp = vals["exp"].reshape(
                    len(self.benchmarks), len(self.depths), self.reps
                )
            else:
                raise ValueError(
                    f"Array exp has size {exp.size}, expected {len(self.benchmarks) * len(self.depths) * self.reps}"
                )
        else:
            raise KeyError("'exp' key not found in npz file")
        res = list(r["counts"] for r in vals["res"])
        survival_probs = np.zeros(exp.shape)

        for i, bench in enumerate(self.benchmarks):
            for j, counts in enumerate(res):
                depth = int(j // self.reps)
                rep = int(j % self.reps)
                survival_probs[i, depth, rep] = sum(
                    list(
                        int(counts[str(key)]) / self.shots
                        for key in counts
                        if str(key)[
                            len(str(key))
                            - bench[len(bench) - 1]
                            - 1 : len(str(key))
                            - bench[0]
                        ]
                        == str(exp[i, depth, rep])
                    )
                )

            print(f"RB on qubit(s) {bench}")
            print(list(np.around(np.mean(probs), 3) for probs in survival_probs[i]))

        with open(report_file, "w", encoding="utf-8") as fid:
            fid.write(f"survival_probs: {survival_probs}")
