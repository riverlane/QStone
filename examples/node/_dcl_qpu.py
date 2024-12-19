"""Example for Riverlane Deltaflow Control based control systems."""

from typing import Any

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
        dev.connect("172.16.100.118")
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
        dev.disconnect()

    def _get_results(self):
        """This function should run the programme"""
        # Use self.qpu_cfg.num_required_qubits
        outcomes = {}
        value = (1 << self.qpu_cfg.num_required_qubits) - 1
        for i in range(value):
            outcomes[bin(i)[2:].zfill(self.qpu_cfg.num_required_qubits)] = 10
        return outcomes

    def exec(self, qasm: str, shots: int) -> dict:
        """Model running time of circuit"""
        transpiled = self._qasm_to_internal(qasm)
        self._run(transpiled, shots, blocking=True)
        return self._get_results()
