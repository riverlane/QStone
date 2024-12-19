""" Type 0 computations steps. """

import os

import numpy
from pandera import Check, Column, DataFrameSchema

from qstone.connectors import connector
from qstone.steps.computation import Computation
from qstone.utils.utils import ComputationStep, trace


class ExampleComputation(Computation):
    """Your docstring here"""

    # Define the profiling trace display name of your computation script.
    COMPUTATION_NAME = "TYPE0"

    # Defien the path to your json confugration of your computation.
    CFG_STRING = """
    {
      "cfg":
      {
         "num_required_qubits" : 2,
         "repetitions" : 10
      }
    } 
    """

    # Define the schema for validating the parameters of your configuration.
    SCHEMA = DataFrameSchema(
        {
            "num_required_qubits": Column(int, Check(lambda s: s >= 0)),
            "repetitions": Column(int, Check(lambda s: s >= 0)),
        }
    )

    def __init__(self, cfg: dict):
        super().__init__(cfg)

        # Declare your configuraiton parameters here
        self.num_required_qubits: int
        self.repetitions: int

        # Implement your initilisaiton of the computation, define the
        # required QPU configuration needed to run your computation.
        self.qpu_cfg.num_required_qubits = self.num_required_qubits

    # Implement the preprocessing, running and postprocessing steps of your
    # computation in the methods below. The datapth is a path to a common directory
    # you can read and write to between steps. You might want to include the job id
    # 'os.environ['JOB_ID']' to any files your write to prevent file overwriting between
    # running jobs.

    # Implement the preprocessing step of your computation step, for instance
    # you can generate the circuit you want to run here.
    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """Your docstring here"""

    # Implement the running step of your computation. Your circuit can be run by passsing
    # the path to the circuit file to to the connection.run method along with the number of times you want
    # want to execute your circuit. Measurements are returned a dictionary of bitstring frequencies.
    # E.g. {"00" : 1, "01": 3}
    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.RUN)
    def run(self, datapath: str, connection: connector.Connector):
        """Your docstring here"""

        # measurements =connection.run(qasm=circuit_path, reps=100)

    # Implement the postproecessing step of your computation step with the measurements
    # of your computation.
    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Your docstring here"""
