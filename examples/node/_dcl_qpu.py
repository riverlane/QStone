"""Example for Riverlane Deltaflow Control based control systems."""

from typing import Any
import numpy as np
import time
import re
import random

try:
    from dcl.device import Device
    from dcl.components.shared_data_types import SinePulse, SquareEnvelope, PMTWindow
    from dcl.batch import Batch
except ImportError:
    print("DCL library not installed - skipping")

from _qpu import QPU, QpuConfiguration


class DCL_QPU(QPU):
    """DCL based QPU. Class."""

    def __init__(self):
        qpu_cfg = QpuConfiguration()
        qpu_cfg.num_required_qubits = 4
        super().__init__(qpu_cfg)

    def _qasm_to_internal(self, qasm: str) -> Any:
        """This function should transpile from QASM to native (if required)"""
        cmds = []
        for line in qasm.splitlines():
            line = line.upper()
            if line.startswith(("RZ", "RX")):
                index1 = int(line[line.find("[") + 1 : line.find("]")])
                cmds.append(("pi_over_2_pulse", index1))
            elif line.startswith(("CNOT", "CZ")):
                index1 = int(line[line.find("[") + 1 : line.find("]")])
                start = line.find("]") + 1
                index2 = int(line[line.find("[", start) + 1 : line.find("]", start)])
                cmds.append(("pi_pulse", index1, index2))
            elif line.startswith("qubit["):
                self.qpu_cfg.num_required_qubits = int(
                    line[line.find("[") + 1 : line.find("]")]
                )
        return cmds

    def _run(self, program: Any, shots: int, blocking: bool):
        """This function should run the programme"""

        # Initialisation
        dev = Device()
        # dev.connect("172.16.100.118")
        dev.connect("192.168.1.202")
        # Channels
        dds1 = dev.base.rf_out[1]
        dds2 = dev.base.rf_out[2]
        pmt0 = dev.base.dig_in[1]
        # Pulses
        US = 1_000
        readout_pulse = SinePulse(
            name="readout",
            frequency=100e6,
            amplitude_scale=1.0,
            amplitude_envelope=SquareEnvelope(pulse_length=10000),
        )
        window = PMTWindow(length=readout_pulse.length, threshold=3)
        pi_over_2_pulse = SinePulse(
            name="pi_over_2_pulse",
            frequency=100e6,
            amplitude_scale=1.0,
            amplitude_envelope=SquareEnvelope(pulse_length=1000),
        )
        pi_pulse = SinePulse(
            name="pi_pulse",
            frequency=50e6,
            amplitude_scale=1.0,
            amplitude_envelope=SquareEnvelope(pulse_length=2000),
        )
        batch = Batch()

        # Perform measurement
        for inst in program:
            # temporarly ignoring indexing
            if "pi_pulse" in inst:
                batch.add(dds1.channel[0].gen_pulse_cmd(pi_pulse))
                batch.advance_cursor(pi_pulse.length)
            elif "pi_over_2_pulse" in inst:
                batch.add(dds2.channel[0].gen_pulse_cmd(pi_over_2_pulse))
                batch.advance_cursor(pi_over_2_pulse.length)
            batch.advance_cursor(4)
        batch.add(pmt0.readout_cmd(window))
        batch.advance_cursor(window.length)
        batch.advance_cursor(window.length)
        _batch_result = dev.run_batch(batch)
        time.sleep(0.05)
        dev.disconnect()

    def _get_results(self, num_measured_qubits, shots):
        """This function should run the programme"""
        # Use self.qpu_cfg.num_required_qubits
        outcomes = {}
        value = (1 << num_measured_qubits)
        remaining = int(shots)
        for i in range(value - 1):
            if remaining > 0:
                outcomes[bin(i)[2:].zfill(num_measured_qubits)] = np.random.randint(0, remaining)
                remaining -= outcomes[bin(i)[2:].zfill(num_measured_qubits)]
            else:
                outcomes[bin(i)[2:].zfill(num_measured_qubits)] = 0
        outcomes[bin(value - 1)[2:].zfill(num_measured_qubits)] = remaining
        return outcomes


    def _get_qasm_circuit_random_sample(self, qasm, shots):
        """Mocks simulation of qasm circuit by giving random readouts for classical registers

        Args:
            qasm: string representation of qasm circuit
            shots: number of readouts to simulate
        Returns frequency of each classical bit string sampled
        """
        # Extract number classical registers
        creg_defs = re.findall(r"creg [a-zA-Z]\w*\[\d+\]", qasm)
        num_cregs = int(re.findall(r"\d+", creg_defs[0])[0])

        # Extract the mapping between quantum and classical registers
        mapping = []
        qreg_meas = re.findall(r"[a-zA-Z]\w*\[\d+\] -> ", qasm)
        for qreg in qreg_meas:
            trimmed = qreg[len("q[")]
            mapping.append(int(re.findall(r"\d+", trimmed)[0]))

        # Generate a random readout per shot
        measurements = []
        counts = {}
        for i in range(shots):
            meas = list(list(random.randint(0,1) for _ in range(num_cregs)))
            key = ''.join(str(bit) for bit in meas)
            measurements.append(meas)
            if key not in counts.keys(): counts[key] = 1
            else: counts[key] += 1

        return {'mapping': mapping, 'measurements': measurements, 'counts': counts, 'mode': 'random source'}


    def exec(self, qasm: str, shots: int) -> dict:
        """Model running time of circuit"""
        transpiled = self._qasm_to_internal(qasm)
        self._run(transpiled, shots, blocking=True)
        return self._get_qasm_circuit_random_sample(qasm, shots)
