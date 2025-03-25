## What

An utility to benchmark the quality of an HPC and Quantum Computers integration. The benchmark allows the definition of a set of users for which a set of configurable quantum applications will be randomly selected. Example of currently supported quantum applications: VQE, PyMatching, RB. Users can create custom applications and use them together with the core applications.
QStone generates different portable files (.tar.gz), each supporting a different user and a different scheduler (currently supporting: slurm, lsf, bare_metal). During execution of the benchmark, QStone gathers information on each steps of the applications, allowing investigations on bottlenecks and/or resource constraints at the interface between Quantum and HPC.
The benchmark under the following [assumptions](ASSUMPTIONS.md).

## Why

Building an appropriate hardware/software infrastructure to support HPCQC requires
loads of work. We believe we shoud use a data driven approach in which we measure, fix, measure again with every new version of Quantum Computers, software and HPC hardware.

## Where

Currently supported platforms/architectures:

- MacOS: M1/M2 (Sequoia)
- Intel: x86 (Ubuntu)
- PowerPC: Power9 (RedHat)

Tested on Python [3.9-3.12]

## How

### Installation

`pip install QStone`

To leverage MPI features, first install OpenMPI.

`sudo apt install openmpi` [On Ubuntu]
`sudo yum install openmpi` [On Debian Systems]
`brew install openmpi` [On Mac]
 
Followed by a full installation:

`pip install QStone[mpi]`

### Execution

Run QStone using Command Line Interface

- Run the **generator** command

  `qstone generate -i conf.json [--atomic/-a] [--scheduler/-s "slurm"/"jsrun"/"bare_metal"]`

  Generates tar.gz files that contains all the scripts to run scheduler for each user. Currently supported schedulers: [baremetal, altair/fnc, slurm/schedmd]. QStone expects an input configuration describing the users to want to generate jobs for as well as the description of the quantum computer you are generating jobs for. The optional `--atomic` flag forces the generation of single step jobs, instead of the default repartition in three jobs (pre, run, post). The `-s` flag allows selecting the output scheduler, default is `bare_metal`.

  With `config.json`:

```json
{
  "environment": { 
     "project_name": "proj_name",
     "scheduling_mode" : "LOCK",
     "job_count": 5,
     "qpu" : {
        "mode" : "RANDOM"
     },
     "connectivity": {
     	"mode": "NO_LINK",
     	"qpu": {
           "ip_address": "0.0.0.0",
     	   "port": 55
        }
     },
     "timeouts" : {
         "http": 5,
         "lock": 4
     } 
  },
  "jobs": [
    {
      "type": "VQE",
      "qubits": [4, 6],
      "num_shots": [100, 200],
      "walltime" : 10,
      "nthreads" : 4
    },
    {
      "type": "RB",
      "qubits": [2],
      "num_shots": [100],
      "walltime" : 10,
      "nthreads" : 2
    },
    {
      "type": "QBC",
      "qubits": [4],
      "num_shots": [32],
      "walltime": 20,
      "nthreads" : 2
    }
  ],
  "users": [
    {
      "user": "user0",
      "computations": {
        "VQE": 0.05,
        "RB": 0.94,
        "PyMatching": 0.01
      }
    }
  ]
}
```

For more information on the `config.json` format refer to the associated [json schema](qstone/utils/config_schema.py).
Among the other things, the config file allows setting different polling/querying/scheduling policies for handling shared access to the QPU.
Only SLURM currently supports the high-performance (lowest-latency) "SCHEDULER" mode" please refer to [SLURM](SLURM.md) for more information.

- Alternatively call the generator in script:

```python
from qstone.generators import generator

def main():
    generator.generate_suite(config="config.json",
        job_count=100, output_folder=".", atomic=False, scheduler="bare_metal")

if __name__ == "__main__":
     main()
```

- Run the **run** command to execute chosen scheduler/workload selecting an optional output folder

  `qstone run -i scheduler.qstone.tar.gz [-o folder]`

The optional `-o` allows selecting the output folder in which to run the benchmark instance.

- Alternatively may untar on your machine of choice and run as the selected user.

  - Run the jobs by executing `sh qstone_suite/qstone.sh`

  - Run the profiling tool to extract metrics of interest.

- Run the **profile** command providing the initial input configuration and output folder to run profiling tool on run information

  `qstone profile --cfg conf.json --folder qstone_profile`

- Run the **profile** command providing the initial input configuration and multiple output folders (in case of multi-user run) to run profiling tool on run information

  `qstone profile --cfg conf.json --folder qstone_profile --folder qstone_profile2`

### Supported backend connectivities

- Local no-link runner
- gRPC
- Http
- Rigetti

### Examples

- Getting started [notebook](examples/running/getting_started.ipynb)
- How to add a [new type of computation](examples/adding/computation/README.md)
- How to create a simple [gateway](examples/node/README.md)

### Contributing

Guidance on how to [contribute](contributing.md) and [change logs](changelog.md)
