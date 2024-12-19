""" Example file to emulate a QPU node """

import calendar
import time

from optparse import OptionParser
import threading
from collections import deque
from flask import Flask, jsonify, request
from _mock_qpu import Mock_QPU
from _dcl_qpu import DCL_QPU
from _qpu import QPU

app = Flask(__name__)

job_queue = deque()
job_queue_lock = threading.Lock()

job_results = {}
job_results_condition = threading.Condition()

# Loop condition for job processor thread
node_active = True


QPU_LIST = {"mock": Mock_QPU(), "dcl": DCL_QPU()}

# Default value
qpu: QPU = Mock_QPU()
qpu_type = None


# Change to your host address here
ADDRESS = "0.0.0.0"
PORT = 10001


@app.route("/qpu/config", methods=["GET"])
def get_qpu_config():
    """API for obtaining QPU configuration.

    Returns QPU configuration as a json.
    """
    print(qpu.qpu_cfg.__dict__)
    return jsonify(qpu.qpu_cfg.__dict__)


@app.route("/execute", methods=["POST"])
def add_job():
    """ "API for submitting QPU job.

    Request args:
        circuit: qasm circuit string
        reps: numbers of times to repeat circuit (shots)
        pkit_id: identifier for circuit
    """
    try:
        data = request.get_json()
        circuit = data["circuit"]
        num_shots = data["reps"]
        job_id = data["pkt_id"]
        with job_queue_lock:
            job_queue.append({"pkt_id": job_id, "circuit": circuit, "reps": num_shots})

        return jsonify({"job_id": job_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/results", methods=["GET"])
def job_result():
    """API for obtaining QPU computation resullt

    Request args:
        pkt_id: identifier for circuit
    """  #
    try:
        data = request.get_json()
        job_id = data["pkt_id"]

        with job_results_condition:
            while job_id not in job_results:
                job_results_condition.wait()
            # Direct mapping
            mapping = list(range(len(job_results[job_id][0])))
            timestamp = calendar.timegm(time.gmtime())
            origin = qpu_type
            message = {
                "mapping": mapping,
                "measurements": job_results[job_id],
                "mode": "random source",
                "timestamp": timestamp,
                "origin": origin,
            }
            return jsonify(job_results[job_id]), 200

    except Exception as e:
        print(f"Error: - {str(e)}")
        return jsonify({"error": str(e)}), 500


def process_jobs(qpu: QPU = Mock_QPU()):
    """Worker thread for processing and running job on QPU"""
    job = None
    while node_active:
        with job_queue_lock:
            if job_queue:
                job = job_queue.popleft()
        if job is None:
            time.sleep(1)
            continue

        circuit_id = job["pkt_id"]
        circuit = job["circuit"]
        num_shots = job["reps"]

        result = qpu.exec(circuit, num_shots)

        with job_results_condition:
            job_results[circuit_id] = result
            job_results_condition.notify_all()
        job = None


def main():
    global qpu, qpu_type
    parser = OptionParser()
    parser.add_option("-t", "--type", dest="type", help="Type of node", default="mock")
    (opts, args) = parser.parse_args()
    qpu = QPU_LIST[opts.type]
    qpu_type = opts.type
    threading.Thread(target=process_jobs, args=(qpu,)).start()
    app.run(debug=False, host=ADDRESS, port=PORT)


if __name__ == "__main__":
    main()
