""" QBC computations steps. """

import os

import numpy
from scipy.optimize import minimize
from pandera import Check, Column, DataFrameSchema
import json
import ast

from qstone.connectors import connector
from qstone.apps.computation import Computation
from qstone.utils.utils import ComputationStep, trace

from mpi4py import MPI

@trace(computation_type="QBC", computation_step=ComputationStep.RUN, label="QASM_GENERATION")
def generate_vqc_qasm(pqc_number, num_qubits, datum, parameters):
    '''
    Generates text for a qasm file of a Quantum Circuit (QC) consisting of encoding layers encoding a datum
    and Variational Quantum Circuit (VQC) with trainable parameters.
    The encoding layers are Rz and Rx layers at the beggining and end of the QC taking the datum as rotational angles.
    The VQC form can be chosen via pqc_number = {2, 5, 15}
    The pqc_number parameters references the QCs with the same number in figure 2 of Adv. Quantum Technol. 2019, 2, 1900070
    '''

    qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{num_qubits}];\ncreg c[1];'
    for q in range(num_qubits): qasm += f'rx({datum[2*q]}) q[{q}]\n'
    for q in range(num_qubits): qasm += f'rz({datum[2*q+1]}) q[{q}]\n'

    if pqc_number == 2:
        for q in range(num_qubits): qasm += f'rx({parameters[q]}) q[{q}]\n'
        for q in range(num_qubits): qasm += f'rz({parameters[num_qubits+q]}) q[{q}]\n'
        for q in range(num_qubits-1): qasm += f'CNOT q[{q}] q[{(q+1)}]\n'

    if pqc_number == 5:
        for q in range(num_qubits): qasm += f'rx({parameters[q]}) q[{q}]\n'
        for q in range(num_qubits): qasm += f'rz({parameters[num_qubits+q]}) q[{q}]\n'
        qasm += "gate crz(lambda) a,b\n{\nu1(lambda/2) b;\ncx a,b;\nu1(-lambda/2) b;\ncx a,b;\n}"
        i=0
        for q in range(num_qubits):
            for qc in range(num_qubits):
                if q != qc:
                    qasm += f'crz({parameters[2*num_qubits+i]}) q[{q}] q[{(qc)}]\n'
                    i+=1
        for q in range(num_qubits): qasm += f'rx({parameters[(num_qubits+1)*num_qubits+q]}) q[{q}]\n'
        for q in range(num_qubits): qasm += f'rz({parameters[(num_qubits+2)*num_qubits+q]}) q[{q}]\n'

    if pqc_number == 15:
        for q in range(num_qubits): qasm += f'ry({parameters[q]}) q[{q}]\n'
        for q in range(num_qubits): qasm += f'CNOT q[{q}] q[{(num_qubits-1+q)%num_qubits}]\n'
        for q in range(num_qubits): qasm += f'ry({parameters[num_qubits+q]}) q[{q}]\n'
        for q in range(num_qubits): qasm += f'CNOT q[{(num_qubits-q)}] q[{(num_qubits+1-q)%num_qubits}]\n'

    #for q in range(num_qubits): qasm += f'rx({datum[2*q+1]}) q[{q}]\n'
    qasm += "measure q[0] -> c[0];\n"

    return qasm


@trace(computation_type="QBC", computation_step=ComputationStep.RUN, label="MPI_COMMUNICATION")
def mpi_communication(data, comm, bcast=True):

    if bcast==True: return comm.Bcast([data, MPI.DOUBLE], root=0)
    elif bcast==False: return comm.allreduce(data, op=MPI.SUM)


@trace(computation_type="QBC", computation_step=ComputationStep.RUN, label="LOSS_COMPUTATION")
def loss(parameters, pqc_number, num_qubits, shots, data, labels, idxs, comm, run_file, connection):

    training_size = len(data)
    loss = 0

    #comm.Bcast([parameters, MPI.DOUBLE], root=0)
    mpi_communication(parameters, comm)

    for i in idxs:
        path = os.path.join(os.path.dirname(run_file), f"qbc_{os.environ['JOB_ID']}_{str(i)}.qasm")

        datum = data[i]
        qasm = generate_vqc_qasm(pqc_number, num_qubits, datum, parameters)

        with open(path, "w", encoding="utf-8") as fid: fid.write(qasm)
        response = connection.run(qasm=path, reps=shots)
        #if isinstance(response, str) == True or ('real_data' in response.keys() and response['real_data'] == False):
        meas_bits = list("0".join("" for j in range(1-len(bin(k)[2:])+1)) + bin(k)[2:] for k in range(pow(2,1)))
        counts = {}
        num_keys = len(meas_bits)
        remaining = shots
        for j in range(num_keys-1):
            if remaining > 0:
                counts[meas_bits[j]] = numpy.random.randint(0, remaining)
                remaining -= counts[meas_bits[j]]
            else: counts[meas_bits[j]] = 0
        counts[meas_bits[-1]] = remaining
        #elif 'real_data' in response.keys() and response['real_data'] == True: counts = response['counts']

        probs = {key: counts[key]/training_size/shots for key in counts.keys()}
        loss -= probs[str(labels[i])]
    print('partial loss for rank {}: {}'.format(comm.Get_rank(), loss), flush=True)
    #temp = comm.allreduce(loss, op = MPI.SUM)
    temp = mpi_communication(loss, comm, bcast=False)
    loss = temp
    print('total loss: {}'.format(loss), flush=True)

    return loss


class QBC(Computation):
    """
    QBC computation class.
    """

    COMPUTATION_NAME = "QBC"
    CFG_STRING = """
    {
      "cfg":
      {
        "num_required_qubits" : 4,
        "pqc_number" : 2,
        "training_size" : 20,
        "max_iters" : 10,
        "shots" : 64
      }
    }
    """
    SCHEMA = DataFrameSchema(
        {
            "pqc_number": Column(int, Check(lambda s: s >= 0)),
            "training_size": Column(int, Check(lambda s: s >= 0)),
            "max_iters": Column(int, Check(lambda s: s >= 0)),
            "shots": Column(int, Check(lambda s: s >= 0)),
        }
    )


    def __init__(self, cfg: dict):
        super().__init__(cfg)

        self.num_required_qubits: int
        self.repetitions: int
        self.training_size: int
        self.max_iters: int
        self.shots: int
        self.pqc_number: int
        
        self.qpu_cfg.num_required_qubits = self.num_required_qubits

        comm = MPI.COMM_WORLD
        self.comm = comm
        self.size = comm.Get_size()
        self.rank = comm.Get_rank()

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE, label="DATA_GENERATION")
    def pre(self, datapath: str):
        """Generates a random two-class dataset to train a Quantum Binary Classifier"""
        
        run_file = f"{datapath}/qbc_run_{os.environ['JOB_ID']}.npz"

        if self.rank == 0:
            data = numpy.pi * numpy.random.rand(self.training_size, 2*self.num_required_qubits)
            labels = numpy.array([0] * (self.training_size//2 + self.training_size%2) + [1] * (self.training_size//2))
            numpy.random.shuffle(labels)
        
            numpy.savez(run_file, data=data, labels=labels, allow_pickle=True)
        
        comm.Barrier()


    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.RUN, label="MODEL_TRAINING")
    def run(self, datapath: str, connection: connector.Connector):
        """Runs the VQC optimization"""
        
        run_file = f"{datapath}/qbc_run_{os.environ['JOB_ID']}.npz"
        
        model = numpy.load(run_file, allow_pickle=True)
        data = model['data']
        labels = model['labels']

        jobs_per_rank = self.training_size // self.size
        leftover = self.training_size % self.size
        if self.rank > self.size-leftover-1: jobs_per_rank += 1
        jobsizes = self.comm.allgather(jobs_per_rank)
        starts = list(sum(jobsizes[:i]) for i in range(len(jobsizes)))
        idxs = numpy.arange(starts[self.rank], starts[self.rank] + jobsizes[self.rank])

        totqasms = []
        totresults = []
        totlosses = []
        if self.pqc_number in [2,15]: totparameters = 2 * numpy.pi * numpy.random.rand(2*self.num_required_qubits)
        if self.pqc_number == 5: totparameters = 2 * numpy.pi * numpy.random.rand(pow(self.num_required_qubits,2)+3*self.num_required_qubits)

        #self.comm.Bcast([totparameters, MPI.DOUBLE], root=0)
        mpi_communication(totparameters, self.comm)

        #print('Training QBC...\n')
        result = minimize(loss, totparameters, args=(self.pqc_number, self.num_required_qubits, self.shots, data, labels, idxs, self.comm, run_file, connection),
                          method='COBYLA', options={'maxiter':self.max_iters})
        print('x0', totparameters)
        for key in result.keys():
            print(key, result[key])
        store = {"data": data, "labels": labels, "result": result}
        if self.rank == 0: numpy.savez(run_file, **store, allow_pickle=True)


    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Post process run result"""

        if self.rank == 0:
            run_file = f"{datapath}/qbc_run_{os.environ['JOB_ID']}.npz"
            print(f"Training results at {run_file}\n")

        comm.Barrier()
