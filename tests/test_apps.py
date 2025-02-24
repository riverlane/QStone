"""Tests for computation types"""

import os
import shutil

import glob
import numpy as np
import pytest
import shutil

from qstone.connectors import connector
from qstone.apps import get_computation_src

def _get_file(regex):
    return glob.glob(regex)[0]

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
    with pytest.raises(Exception) as e_info:
        compute_src = get_computation_src("RB").from_json()
        # This should fail due to the lack of npz file
        profile_file = os.path.join(tmp_path, "job_test_POST_RB*.json")
        compute_src.post(tmp_path)
        print(os.listdir(tmp_path))
        with open(_get_file(profile_file), "r") as fir:
            assert '"success": false' in fir.read()


def test_pre_RB(tmp_path, env):
    tmp_path.mkdir(exist_ok=True)
    run_file = tmp_path / "RB_run_test.npz"
    compute_src = get_computation_src("RB").from_json()
    compute_src.pre(tmp_path)

    # Check profile file
    profile_file = os.path.join(tmp_path, "job_test_PRE_RB.json")
    with open(_get_file(profile_file), "r") as fir:
        assert '"success": true' in fir.read()
    assert compute_src.num_shots == 12, "Wrong number of shots"
    # Check generated file
    vals = np.load(run_file)
    assert len(vals["qasms"]) == 40
    assert len(vals["exp"]) == 40

def test_post_RB(tmp_path, env):
    shutil.copyfile("tests/data/apps/RB_run_test.npz", tmp_path / "RB_run_test.npz")
    compute_src = get_computation_src("RB").from_json()
    report_file = tmp_path / "RB_report_test.txt"
    compute_src.post(tmp_path)
    assert os.path.isfile(report_file)


def test_call_pre_PyMatching(tmp_path, env):
    """Test execution of pre step of PyMatching computation"""
    compute_src = get_computation_src("PyMatching").from_json()
    compute_src.pre(tmp_path)
    assert compute_src.num_shots == 12, "Wrong number of shots"


def test_pre_PyMatching_writes_stim(tmp_path, env):
    """Test stim circuit write pre step of PyMatching computation"""
    compute_src = get_computation_src("PyMatching").from_json()
    circuit_path = compute_src.pre(tmp_path)
    expected_stim = f"{circuit_path}.stim"
    assert os.path.exists(expected_stim)


def test_pre_PyMatching_writes_qasm(tmp_path, env):
    """Test qasm circuit write pre step of PyMatching computation"""
    compute_src = get_computation_src("PyMatching").from_json()
    circuit_path = compute_src.pre(tmp_path)
    expected_qasm = f"{circuit_path}.qasm"
    assert os.path.exists(expected_qasm)


@pytest.mark.depends(on=["test_call_pre_PyMatching"])
def test_call_run_PyMatching(tmp_path, env):
    """Test execution of run step of PyMatching computation"""
    compute_src = get_computation_src("PyMatching").from_json()
    compute_src.pre(tmp_path)
    compute_src.run(
        tmp_path, connector.Connector(connector.ConnectorType.NO_LINK, "0", "0", None)
    )
    assert compute_src.num_shots == 12, "Wrong number of shots"


def test_PyMatching_writes_syndromes(tmp_path, env):
    """Test syndrome write run step of PyMatching computation"""
    compute_src = get_computation_src("PyMatching").from_json()
    compute_src.pre(tmp_path)
    syndrome_path = os.path.join(
        tmp_path, f"PyMatching_{os.environ['JOB_ID']}_syndromes.npz"
    )
    compute_src.run(
        tmp_path, connector.Connector(connector.ConnectorType.NO_LINK, "0", "0", None)
    )
    compute_src.post(tmp_path)
    print(os.listdir(tmp_path))
    assert os.path.exists(syndrome_path)


@pytest.mark.depends(on=["test_call_run_PyMatching"])
def test_call_post_PyMatching(tmp_path, env):
    """Test execution of post step of PyMatching computation"""
    compute_src = get_computation_src("PyMatching").from_json()
    compute_src.pre(tmp_path)
    compute_src.run(
        tmp_path, connector.Connector(connector.ConnectorType.NO_LINK, "0", "0", None)
    )
    compute_src.post(tmp_path)


def test_call_pre_QBC(tmp_path, env):
    """Test execution of pre step of QBC computation"""
    compute_src = get_computation_src("QBC").from_json()
    # Initialise
    compute_src.rank = 0
    compute_src.pre(tmp_path)
    data_path = os.path.join(tmp_path, f"qbc_run_{os.environ['JOB_ID']}.npz")
    assert os.path.exists(data_path)


@pytest.mark.depends(on=["test_call_pre_QBC"])
def test_call_run_QBC(tmp_path, env):
    """Test execution of run step of QBC computation"""
    compute_src = get_computation_src("QBC").from_json()
    # Initialise
    compute_src.rank = 0
    data_path = os.path.join(tmp_path, f"qbc_run_{os.environ['JOB_ID']}.npz")
    shutil.copyfile("tests/data/apps/qbc_run_test.npz", data_path)
    compute_src.run(
        tmp_path, connector.Connector(connector.ConnectorType.NO_LINK, "0", "0", None)
    )
    model = np.load(data_path, allow_pickle=True)
    print(model)
    assert os.path.exists(data_path)


@pytest.mark.depends(on=["test_call_run_QBC"])
def test_call_post_QBC(tmp_path, env):
    """Test execution of post step of QBC computation"""
    compute_src = get_computation_src("QBC").from_json()
    # Initialise
    compute_src.rank = 0
    data_path = os.path.join(tmp_path, f"qbc_run_{os.environ['JOB_ID']}.npz")
    shutil.copyfile("tests/data/apps/qbc_run_test.npz", data_path)
    compute_src.post(tmp_path)
    assert os.path.exists(data_path)


def test_pre_custom_app(tmp_path, env):
    """capability to call custom application"""
    compute_src = get_computation_src("tests.data.apps.custom1.Custom1").from_json()
    compute_src.pre(tmp_path)
    assert os.path.exists(os.path.join(tmp_path, "pre.txt"))
