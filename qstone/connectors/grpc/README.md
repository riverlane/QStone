# Regenerating proto files

To regenerate proto files run from this folder:
>> python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. qpu.proto -I .

