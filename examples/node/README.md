### QPU compute node
This is a simple server to provide an interface for a QPU that can be used by QStone.

## Installation

To install:
- Follow QStone installation
- Install flask (pip or poetry)
- Check test run `pytest "examples/node/tests"`
- Define the `PORT` and  `ADDRESS` in `remote_qpu.py`
- Start the server `python remote_qpu.py`

## Usage

To use the example provided as a mock remote node (i.e. to validate connectivity, network setup etc) clone the repository and follow the installation procedure on the remote node. 
Next modify your `conf.json` to point to the flask server:

```json
{
    "project_name" : "proj_name",     
    "connector" : "NO_LINK",
    "qpu_ip_address" : "http://REPLACE_WITH_ADDRESS",
    "qpu_port" : "REPLACE_WITH_PORT",
    "num_required_qubits" : 4,
    "users" : [
        {
        "user": "user0",
        "weight" : 0.2,
        "computations" : 
            {
            "type0": 0.05,
            "type1": 0.94,
            "type2": 0.01
            }
        },
        {
        "user": "user1",
        "weight" : 0.3,
        "computations" : 
             {
             "type0": 0.10,
             "type1": 0.85,
              "type2": 0.05
             }
        }
   ]
}
```
 
