"""Tests for computation types"""

import os
import shutil

import numpy as np
import pytest

from qstone.simulators.qutip_sim import QuTiPSim


@pytest.fixture()
def env(tmp_path):
    """Fixture to set environment variables"""
    os.environ["JOB_ID"] = "test"
    os.environ["PROG_ID"] = "test"
    os.environ["QS_USER"] = "test"
    os.environ["PROFILE_PATH"] = str(tmp_path.absolute())
    os.environ["OUTPUT_PATH"] = str(tmp_path.absolute())
    os.environ["NUM_QUBITS"] = "2"
    os.environ["NUM_SHOTS"] = "12"


def test_app_logs_failures(tmp_path, env):
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[4];
    creg c[4];
    x q[0];
    x q[1];
    x q[2];
    x q[3];
    cx q[0], q[1];
    cx q[2], q[3];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    measure q[2] -> c[2];
    measure q[3] -> c[3];
    """
    measurements = QuTiP().run(qasm)
    assert measurements == ["0", "1", "0", "1"]
