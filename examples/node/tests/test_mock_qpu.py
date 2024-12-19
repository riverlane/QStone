"""Tests for Mock QPU runtime modeler"""

import os
import sys
import pytest

# To include this path to the search path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from _mock_qpu import Mock_QPU


@pytest.fixture
def qpu():
    return Mock_QPU()


def test_mock_qpuclifford_circuit(qpu):
    circuit = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
 
    h q[0];
    cx q[0], q[1];
 
    measure q -> c;
    """
    qpu.exec(circuit, 10)


def test_mock_qpu_syndrome_extraction_circuit(qpu):
    circuit = """
    OPENQASM 2.0;
    include "qelib1.inc";

    qreg q[9];
    creg c[9];
    x q[0];
    x q[2];
    x q[4];
    x q[6];
    x q[8];
    barrier q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8];
    cx q[0], q[1];
    cx q[2], q[1];
    cx q[2], q[3];
    cx q[4], q[3];
    cx q[4], q[5];
    cx q[6], q[5];
    cx q[6], q[7];
    cx q[8], q[7];
    measure q[1] -> c[1];
    measure q[3] -> c[3];
    measure q[5] -> c[5];
    measure q[7] -> c[7];
    barrier q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8];
    reset q[0];
    reset q[2];
    reset q[4];
    reset q[6];
    reset q[8];
    x q[0];
    x q[2];
    x q[4];
    x q[6];
    x q[8];
    barrier q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8];
    cx q[0], q[1];
    cx q[2], q[1];
    cx q[2], q[3];
    cx q[4], q[3];
    cx q[4], q[5];
    cx q[6], q[5];
    cx q[6], q[7];
    cx q[8], q[7];
    measure q[1] -> c[1];
    measure q[3] -> c[3];
    measure q[5] -> c[5];
    measure q[7] -> c[7];
    barrier q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7], q[8];
    """
    qpu.exec(circuit, 10)


def test_mock_qpu_non_clifford_circuit(qpu):
    circuit = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
 
    t q[0];
    cx q[0], q[1];
    t q[1];
    
    measure q -> c;
    """
    qpu.exec(circuit, 10)
