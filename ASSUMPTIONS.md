# Assumptions

## Reasons

The HPC and Quantum integration is at its infancy. QStone makes assumptions (hopefully sound today) that might become wrong in the future. By making them explicit and in plain English we all contributors to understand, suggest and correct the package organically.

## Formats

### Measurements

All the connectors return measurements to the different routines. To allow smooth transition from one connector to another it is key to preserve the same data format. We currently return a Python dictionary with the following structure:

```python
   {
    "mapping": [], # A list of indexes to map qubit number into measurement number. 
    "measurements" : [[],[],[]], # A list of lists with each inner list representing the classical register value associated to each qubit readout mapped as per "mapping" field. The number of lists should match the required number of shots.
    "mode": "simulated", # Three options, simulated, real, random source
    "timestamp" : UTC, # The timestamp of the measurement at the connector point. 
    "origin": "machine_name" # The name of the machine/system that has generated the data 
   }
```
The `measurements` field for a three qubits measurement operations with qubit 0 and qubit 1 swapped would look like this:
```python
"mapping": [1,0,2]
"measurement": [[0,0,0],[0,1,0],[1,0,1]]
```
Where the first shot returned 0 for qubit0, qubit1 and qubit2, the second shot 1 for qubit0 and 0 for qubit1 and qubit2 and for last shot 0 for qubit0 and 1 for qubit1 and qubit2.

## Core 

### Scheduling

All the benchmarks are by default generated with each application split into three jobs, `pre`, `run` and `post`. `run` is the only phase that actively requires a QPU. This allows resource allocation (similar to GPUs) whenever schedulers understand the concept. For example, in Slurm it is possible to define a generalised resource (GRES) and provide a descriptor file for it. The run job (jsrun) can in this case be scheduled only when the resource becomes available, greatly improving the responsiveness of the system.

## Users

### Language

All the applications use OpenQASM2.0 as core language. We believe it is the most used language and the one that requires the least dependencies to be installed, allowing to run on most architectures.



