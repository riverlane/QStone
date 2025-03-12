"""Defines the two steps of PyMatching jobs"""

import os

import numpy as np
import pymatching
from pandera import Check, Column, DataFrameSchema
from stim import Circuit  # pylint:disable=no-name-in-module

from qstone.apps.computation import Computation
from qstone.connectors import connector
from qstone.utils.utils import ComputationStep, trace


class PyMatching(Computation):  # pylint:disable=invalid-name
    """
    PyMatching computation class.
    """

    COMPUTATION_NAME = "PyMatching"
    CFG_STRING = """
    {
      "cfg":
      {
        "num_required_qubits" : 10,
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

    def _initialise_circuit(self):
        """Initialise the circuit using Stim"""
        circuit = Circuit.generated(
            "surface_code:rotated_memory_x",
            distance=3,
            rounds=5,
            after_clifford_depolarization=0.005,
        )
        model = circuit.detector_error_model(decompose_errors=True)
        matching = pymatching.Matching.from_detector_error_model(model)
        sampler = circuit.compile_detector_sampler()
        return (matching, sampler)

    def _convert_stim_circuit(self, stim_circuit: Circuit):
        """Convert stim circuit to standardised circuit format

        Args:
            circuit: stim circuit object

        Returns: circuit converted from stim circuit to format
        to be used on runner, current standard is QASM
        """
        # Noise not supported in QASM
        noiseless_circuit = stim_circuit.without_noise()
        qasm_circuit = noiseless_circuit.to_qasm(open_qasm_version=3)
        return qasm_circuit

    def generate_synthetic_data(self, data_path: str):
        """Generates synthetic data and stores them in data_path"""
        _, sampler = self._initialise_circuit()
        syndrome, actual_observables = sampler.sample(
            shots=self.num_shots, separate_observables=True
        )
        np.savez(data_path, syn=syndrome, obs=actual_observables)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.PRE)
    def pre(self, datapath: str):
        """Prepare and write circuit for QEC experiment

        Args:
            datapath: path location to write circuit

        Returns: path location of written circuit, without extension
        """
        stim_circuit = Circuit.generated(
            "surface_code:rotated_memory_x",
            distance=3,
            rounds=5,
            after_clifford_depolarization=0.005,
        ).without_noise()

        qasm_circuit = self._convert_stim_circuit(stim_circuit)
        circuit_path = os.path.join(datapath, f"PyMatching_{os.environ['JOB_ID']}")

        # Write qasm circuit
        with open(f"{circuit_path}.qasm", "w", encoding="utf-8") as fid:
            fid.write(str(qasm_circuit))

        # Write stim circuit to extract sampler on run
        with open(f"{circuit_path}.stim", "w", encoding="utf-8") as fid:
            stim_circuit.to_file(fid)

        return circuit_path

    def get_creg_indexes(self, qasm_content: str):
        """
        Parse a QASM file content to determine the indexes of classical registers (cregs)
        assuming first-come-first-serve allocation.

        Args:
            qasm_content (str): Content of the QASM file as a string

        Returns:
            dict: Dictionary mapping creg names to their bit ranges as tuples (start, end)
        """
        # Initialize variables
        creg_info = {}
        current_index = 0

        # Split the content into lines
        lines = qasm_content.strip().split("\n")

        # Process each line
        for line in lines:
            # Remove comments if any
            if "//" in line:
                line = line[: line.index("//")]

            line = line.strip()

            # Look for creg declarations
            if line.startswith("creg "):
                # Extract the creg name and size
                # Format is typically: creg name[size];
                parts = line.replace("creg ", "").replace(";", "").strip().split("[")
                if len(parts) == 2:
                    creg_name = parts[0].strip()
                    size_part = parts[1].split("]")[0].strip()

                    try:
                        size = int(size_part)
                        # Calculate the index range for this creg
                        start_index = current_index
                        end_index = current_index + size - 1

                        # Store the information
                        creg_info[creg_name] = (start_index, end_index)

                        # Update the current index for the next creg
                        current_index += size
                    except ValueError:
                        # Skip if size is not a valid integer
                        continue

        return creg_info

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.RUN)
    def run(self, datapath: str, connection: connector.Connector):
        """Runs the Quantum circuit N times

        Args:
            datapath: path location to write circuit
            connection: connector object to run circuit
            shots: number of shots to be executed

        Returns: path location of syndromes file
        """

        circuit_path = os.path.join(datapath, f"PyMatching_{os.environ['JOB_ID']}")

        # Send circuit to connector
        results = connection.run(qasm=f"{circuit_path}.qasm", reps=self.num_shots)

        # Get det and obs indexes
        with open(f"{circuit_path}.qasm", "r", encoding="utf-8") as fid:
            creg_ranges = self.get_creg_indexes(fid.read())

        # Convert syndromes to np array and write to path
        meas = results["measurements"]
        dets_idx = creg_ranges["dets"]
        obs_idx = creg_ranges["obs"]
        syndrome = np.array(meas[dets_idx[0] : dets_idx[1]], dtype=bool)
        obs = np.array(meas[obs_idx[0] : obs_idx[1]], dtype=bool)

        syndrome_path = os.path.join(
            datapath, f"PyMatching_{os.environ['JOB_ID']}_syndromes.npz"
        )

        np.savez(syndrome_path, syn=syndrome, obs=obs)

    @trace(computation_type=COMPUTATION_NAME, computation_step=ComputationStep.POST)
    def post(self, datapath: str):
        """Runs the postprocessing analysis using PyMatching decoder over a given input file

        Args:
            datapath: path location to write circuit

        Returns: number of errors detected
        """

        circuit_path = os.path.join(datapath, f"PyMatching_{os.environ['JOB_ID']}")

        stim_circuit = Circuit.from_file(f"{circuit_path}.stim")

        # Synthetic data from stim circuit
        sampler = stim_circuit.compile_detector_sampler()
        sampled_syndromes, sample_observables = sampler.sample(
            shots=1000, separate_observables=True
        )

        model = stim_circuit.detector_error_model(decompose_errors=True)
        matching = pymatching.Matching.from_detector_error_model(model)
        print(f"MARCO: datapath - {datapath}")
        syndrome_path = os.path.join(
            datapath, f"PyMatching_{os.environ['JOB_ID']}_syndromes.npz"
        )
        vals = np.load(syndrome_path)

        synd = vals["syn"]
        actual_observables = vals["obs"]

        # In case of simulating circuit by generating random readouts PyMatching will fail
        # So we use the sampled syndromes instead
        try:
            predicted_observables = matching.decode_batch(synd)
        except ValueError:
            predicted_observables = sampled_syndromes
            actual_observables = sample_observables

        num_errors = np.sum(np.any(predicted_observables != actual_observables, axis=1))

        return num_errors
