from concurrent import futures

import grpc

import qstone.connectors.grpc.qpu_pb2 as pb2
import qstone.connectors.grpc.qpu_pb2_grpc as pb2_grpc


class QPUService(pb2_grpc.QPUServicer):
    def __init__(self, *args, **kwargs):
        pass

    def RunQuantumCircuit(self, request, context):
        # get the string from the incoming request
        circuit = request.circuit
        pkt_id = request.pkt_id
        print(f"Circuit received. {circuit}")
        result = '{"00": 1, "01": 9, "10": 80, "11": 10}'
        result = {"result": result, "capacity": 1}
        print(f"Inside RunQuantumCircuit {result}")
        return pb2.CircuitResponse(**result)


class Server:
    def __init__(self, host, port):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc.add_QPUServicer_to_server(QPUService(), self.server)
        self.server.add_insecure_port(f"{host}:{str(port)}")

    def start(self):
        self.server.start()
        print("server.start()")

    def stop(self):
        self.server.stop(None)
