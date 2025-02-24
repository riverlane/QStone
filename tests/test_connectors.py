import json
import os
import threading

import glob
import pytest
from pathlib import Path

# For HTTP connectors
import requests
import requests_mock

import qstone.connectors.grpc.runner as grpc_client
import qstone.connectors.http.runner as http_client

# For GRPC connectors
import tests.mocks.grpc.server as grpc_server
from qstone.connectors.no_link import no_link

# For Rigetti connectors
from qstone.connectors.backends.rigetti import runner as rigetti

def _get_file(regex):
    return glob.glob(regex)[0]

@pytest.fixture()
def env(tmp_path):
    """Connector environment variables setup"""
    os.environ["USER"] = "test"
    os.environ["JOB_ID"] = "test"
    os.environ["QS_USER"] = "test"
    os.environ["PROG_ID"] = "test"
    os.environ["OUTPUT_PATH"] = str(tmp_path)
    os.environ["PROFILE_PATH"] = str(tmp_path)
    os.environ["TIMEOUTS_LOCK"] = "1"
    os.environ["TIMEOUTS_HTTP"] = "1"


def test_no_link_run(tmp_path, env):
    """Test that no link connection runs without error code"""
    mock_circuit = tmp_path / "circuit.qasm"
    with open(mock_circuit, "w", encoding="utf-8") as fid:
        fid.write(
            'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nrx(1.57) q[0];\nmeasure q[0] -> c[0];'
        )
    # Initialise the mock server

    reps = 100
    connection = no_link.NoLinkConnection()
    result = connection.run(mock_circuit, reps, "localhost", 0, None)
    readout_count = sum(result.values())

    # Assert number of readout results is equal to the number of repetitions
    assert readout_count == reps
    # Check that profile file exists
    output_path = os.path.join(tmp_path, "job_test_POST_CONNECTION*.json")
    assert os.path.isfile(_get_file(output_path))


def test_grpc_run(tmp_path, env):
    """Test that grpc connection runs without error code"""

    mock_circuit = tmp_path / "circuit.qasm"
    with open(mock_circuit, "w", encoding="utf-8") as fid:
        fid.write(
            'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nrx(1.57) q[0];\nmeasure q[0] -> c[0];'
        )
    # Initialise the mock server
    print("Starting server")
    server = grpc_server.Server("localhost", 50051)
    server.start()
    reps = 100
    connection = grpc_client.GRPCConnecction()
    result = connection.run(mock_circuit, reps, "localhost", 50051, None)
    server.stop()
    assert result["11"] == 10


def text_callback(request, context):
    context.status_code = 200
    # Returning the values that we expect
    return '{"00": 1, "01": 9, "10": 80, "11": 10}'


@pytest.mark.parametrize(
    "http, retcode, lock, locked, expected",
    [
        ("test.com", 200, None, False, 10),
        ("http://test.com", 503, None, False, None),
        ("test.com", 200, "qstone.lock", False, 10),
        ("http://test.com", 200, "qstone.lock", True, None),
        ("test.com", 200, "anywhere.lock", False, None),
    ],
)
def test_http(tmp_path, env, capsys, mocker, http, retcode, lock, locked, expected):
    """Test that http connection runs without error code"""

    mock_circuit = tmp_path / "circuit.qasm"
    if lock:
        lock = tmp_path / lock
    with open(mock_circuit, "w", encoding="utf-8") as fid:
        fid.write(
            'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nrx(1.57) q[0];\nmeasure q[0] -> c[0];'
        )
    # Mock the timeout
    mocker.patch("qstone.connectors.http.runner.sleep")

    # if testing the file lock block it from outside to mimick another thread
    if locked:
        Path(lock).touch()
        assert os.path.isfile(lock)

    # Register callbacks for the mock
    with requests_mock.Mocker() as mock_request:
        mock_request.post("http://test.com/execute", status_code=retcode)
        mock_request.get("http://test.com/results", text=text_callback)
        # Run the circuit
        reps = 100
        connection = http_client.HttpConnection()
        result = connection.run(mock_circuit, reps, http, None, lock)

    # Remove the file
    if locked:
        os.remove(lock)
        if lock:
            captured = capsys.readouterr()
            assert "QSTONE::ERR - timeout waiting for lock" in captured.err
    else:
        if lock:
            assert not os.path.isfile(lock)

        if expected:
            assert result["11"] == expected
        # Check that profile file exists and contains the custom label
        profile_trace = os.path.join(
            tmp_path, "job_test_RUN_CONNECTION__request_and_process_*.json"
        )
        assert os.path.isfile(_get_file(profile_trace))
        if not locked:
            with open(_get_file(profile_trace), "r", encoding="utf-8") as fid:
                content = fid.read()
                assert '"label": "_request_and_process"' in content


def test_rigetti_run(tmp_path, env, mocker):
    """Test that Rigetti connection runs without error code"""

    mock_circuit = tmp_path / "circuit.qasm"
    with open(mock_circuit, "w", encoding="utf-8") as fid:
        fid.write(
            'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nrx(1.57) q[0];\nmeasure q[0] -> c[0];'
        )
    # Wrap the calls to Rigetti backend not available for testing
    mocker.patch("qstone.connectors.backends.rigetti.runner.RigettiConnection._get_qc")
    mocker.patch("qstone.connectors.backends.rigetti.runner.RigettiConnection._compile")
    mocker.patch("qstone.connectors.backends.rigetti.runner.RigettiConnection._run")
    mocker.patch(
        "qstone.connectors.backends.rigetti.runner.RigettiConnection._get_results",
        return_value=[[1, 1], [1, 1], [0, 0], [0, 0]],
    )
    print("Test")
    connection = rigetti.RigettiConnection()
    result = connection.run(mock_circuit, 10, "8q-qvm", None, None)
    assert result["measurements"][0] == [1, 1]
