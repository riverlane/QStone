"""RB computations steps."""

import os

from pandera import DataFrameSchema

from qstone.connectors import connector
from qstone.apps.computation import Computation
from qstone.utils.utils import ComputationStep, trace


class Custom1(Computation):
    """
    Type 1 computation class.
    """

    COMPUTATION_NAME = "Custom1"
    CFG_STRING = """
    {
    "cfg":
         {
          "num_required_qubits" : 2
         }
    }
    """
    SCHEMA = DataFrameSchema({})

    def __init__(self, cfg: dict):
        super().__init__(cfg)

    @trace(
        computation_type=COMPUTATION_NAME,
        computation_step=ComputationStep.PRE,
        logging_level=0,
    )
    def pre(self, datapath: str):
        with open(os.path.join(datapath, "pre.txt"), "w", encoding="utf-8") as fid:
            fid.write(self._app_args["content"])

    @trace(
        computation_type=COMPUTATION_NAME,
        computation_step=ComputationStep.RUN,
        logging_level=1,
    )
    def run(self, datapath: str, connection: connector.Connector):
        with open(os.path.join(datapath, "run.txt"), "w", encoding="utf-8") as fid:
            fid.write(f"Test")

    @trace(
        computation_type=COMPUTATION_NAME,
        computation_step=ComputationStep.POST,
        logging_level=2,
    )
    def post(self, datapath: str):
        with open(os.path.join(datapath, "post.txt"), "w", encoding="utf-8") as fid:
            fid.write(f"Test")
