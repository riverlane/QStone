"""RB computations steps."""

import os

import numpy as np
import ast
import pygsti
from pandera import Object, Check, Column, DataFrameSchema
from pygsti.processors import CliffordCompilationRules as CCR
from pygsti.processors import QubitProcessorSpec as QPS

from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace


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
         "benchmarks" : [[0],[1],[2],[3]],
         "depths" : [0,2,4,8],
         "reps" : 10,
         "shots": 8
      }
    } 
    """
    SCHEMA = DataFrameSchema(
        {
            "benchmarks": Column(Object,
                                 Check(lambda s: s.apply(lambda x: isinstance(x, list) and
                                                                   all(isinstance(i, list) and all(isinstance(j, int) for j in i) for i in x)))),
            "depths": Column(Object, Check(lambda s: s.apply(lambda x: isinstance(x, list) and all(isinstance(i, int) for i in x)))),
            "reps": Column(int, Check(lambda s: s >= 0)),
            "shots": Column(int, Check(lambda s: s >= 0))
        }
    )


    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.num_required_qubits = int(os.environ.get("NUM_QUBITS", self.num_required_qubits))
        self.benchmarks = ast.literal_eval(os.environ.get("RB_BENCHMARKS", str(self.benchmarks)))
        self.depths = ast.literal_eval(os.environ.get("RB_DEPTHS", str(self.depths)))
        self.reps = int(os.environ.get("RB_REPS", str(self.reps)))
        self.shots = int(os.environ.get("RB_SHOTS", str(self.shots)))


    def _get_allowed_benchmarks(self):
        '''
        Takes the lists of requested randomized benchmarks
        and returns a list with those that can be run simultaneously in a quantum circuit
        '''

        benchs = []
        rejected = []

        for bench in self.benchmarks:
  
            if (bench not in benchs and
                all(x not in [q for ben in benchs for q in ben] for x in bench) and
                all(x < self.num_required_qubits for x in bench)): benchs.append(bench)
            
            else: rejected.append(bench)

        self.benchmarks = benchs


    def _get_configuration(self, bench):
        """
        Returns standard configuration for the RB
        """
        n_qubits = len(bench)
        qubit_labels = list(f"Q{q}" for q in bench)
        gate_names = ["Gxpi2", "Gxmpi2", "Gypi2", "Gympi2"]
        if n_qubits==2:
            gate_names += ["Gcphase"]
            availability = {
                "Gcphase": [tuple(qubit_labels), tuple(qubit_labels[::-1])]
            }
        if n_qubits==1: pspec = QPS(n_qubits, gate_names, qubit_labels=qubit_labels)
        if n_qubits==2: pspec = QPS(n_qubits, gate_names, availability=availability, qubit_labels=qubit_labels)
        compilations = {
            "absolute": CCR.create_standard(
                pspec, "absolute", ("paulis", "1Qcliffords"), verbosity=0
            ),
            "paulieq": CCR.create_standard(
                pspec, "paulieq", ("1Qcliffords", "allcnots"), verbosity=0
            ),
        }
        design = pygsti.protocols.MirrorRBDesign(pspec=pspec,
                                                 clifford_compilations=compilations,
                                                 depths=self.depths,
                                                 circuit_type='clifford',
                                                 circuits_per_depth=self.reps,
                                                 qubit_labels=qubit_labels)
        print(f"Generated benchmarking routing with {n_qubits} qubits")
        return (qubit_labels, pspec, design)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """
        Generates the quantum circuits required to extract
        the survival probability of each requested RB
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"
        self._get_allowed_benchmarks()
        bench_qasms = []
        idealouts = []
        
        for bench in self.benchmarks:
            '''
            Generates qasm files for each allowed RB
            '''
            qubit_labels, _, design = self._get_configuration(bench)
            circuit_list_nested = design.all_circuits_needing_data
            bench_qasms.append([c.convert_to_openqasm(num_qubits=self.num_required_qubits,
                                                standard_gates_version="x-sx-rz",
                                                qubit_conversion=dict(zip(qubit_labels, bench)),
                    )
                    for c in circuit_list_nested
                ]
            )
            idealouts += list(np.concatenate(design.idealout_lists).flat)

        # Here we combine the qasm files of circuits that can be run simultaneosly into one
        qasms = []
        for i in range(len(bench_qasms[0])):
            test = []
            for j in range(len(bench_qasms)):
                temp = list(line for line in bench_qasms[j][i].splitlines() if line != '')
                if j==0: test += temp
                else: test += temp[5:]

            qasms.append(''.join('{}\n'.format(line) for line in test))

        np.savez(run_file, qasms=qasms, exp=idealouts, allow_pickle=True)

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
            results.append(connection.run(qasm=path, reps=self.shots))
        
        store = {"qasms": vals["qasms"], "exp": vals["exp"], "res": results}
        np.savez(run_file, **store, allow_pickle=True)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Runs the processing of the randomised benchmarking using the data provided by
        datapath
        """
        run_file = f"{datapath}/RB_run_{os.environ['JOB_ID']}.npz"
        report_file = f"{datapath}/RB_report_{os.environ['JOB_ID']}.txt"
        self._get_allowed_benchmarks()
        vals = np.load(run_file, allow_pickle=True)
        exp = vals["exp"].reshape(len(self.benchmarks), len(self.depths), self.reps)
        res = list(r['counts'] for r in vals["res"])
        survival_probs = np.zeros(exp.shape)

        for i, bench in enumerate(self.benchmarks):
            for j, counts in enumerate(res):
                depth = j//self.reps
                rep = j%self.reps
                survival_probs[i, depth, rep] = sum(list(value/self.shots for key, value in counts.items()
                                                         if key[len(key)-bench[len(bench)-1]-1:len(key)-bench[0]]==exp[i,depth,rep]))

            print('RB on qubit(s) {}'.format(bench))
            print(list(np.around(np.mean(probs),3) for probs in survival_probs[i]))

        with open(report_file, "w", encoding="utf-8") as fid:
            fid.write(f"survival_probs: {survival_probs}")
