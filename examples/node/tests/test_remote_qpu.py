"""Tests for remote QPU oompute node"""

import os
import sys
import threading

import pytest

# To include this path to the search path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import remote_qpu


@pytest.fixture
def client():
    remote_qpu.app.config["TESTING"] = True
    with remote_qpu.app.test_client() as client:
        yield client


@pytest.fixture
def job_processor():
    remote_qpu.node_active = True
    thr = threading.Thread(target=remote_qpu.process_jobs)
    thr.start()
    yield thr
    remote_qpu.node_active = False
    thr.join()


@pytest.fixture()
def job_data():
    return {
        "circuit": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg c[2];
    
        h q[0];
        cx q[0], q[1];
    
        measure q -> c;
        """,
        "reps": 10,
        "pkt_id": 1,
    }


def test_query_qpu_config(client, job_processor):
    response = client.get("/qpu/config")
    assert response.status_code == 200
    assert response.json == remote_qpu.qpu.qpu_cfg.__dict__


def test_submit_job(client, job_processor, job_data):
    response = client.post("/execute", json=job_data)
    assert response.status_code == 200
    assert len(remote_qpu.job_queue) >= 1

    job_id = response.json["job_id"]
    assert job_id == job_data["pkt_id"]


def test_job_result(client, job_processor, job_data):
    with remote_qpu.job_queue_lock:
        remote_qpu.job_queue.append(job_data)

    response = client.get("results", json=job_data)
    assert response.status_code == 200


def test_multijob_queu_finishes(client, job_processor, job_data):
    JOBS_TO_QUEUE = 10
    with remote_qpu.job_queue_lock:
        for i in range(JOBS_TO_QUEUE):
            remote_qpu.job_queue.append({**job_data, "pkt_id": i})

    for i in range(JOBS_TO_QUEUE):
        response = client.get("results", json={**job_data, "pkt_id": i})
        assert response.status_code == 200
