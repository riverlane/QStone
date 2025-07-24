# QStone

A utility to benchmark the quality of HPC and Quantum Computer integration.

## Overview

QStone allows you to define a set of users for which configurable quantum applications will be randomly selected and executed. The benchmark generates different portable files (`.tar.gz`), each supporting different users and schedulers.

**Currently supported quantum applications:**
- VQE (Variational Quantum Eigensolver)
- PyMatching
- RB (Randomized Benchmarking)
- QBC (Quantum Benchmarking Circuit)

**Key features:**
- Support for custom applications alongside core applications
- Multi-scheduler support (SLURM, LSF, bare metal)
- Detailed performance metrics collection
- Bottleneck and resource constraint analysis at the quantum-HPC interface

The benchmark operates under specific [assumptions](ASSUMPTIONS.md).

## Why QStone?

Building appropriate hardware/software infrastructure for HPCQC requires significant effort. QStone enables a data-driven approach where you can measure performance, implement fixes, and measure again with every new version of quantum computers, software, and HPC hardware.

## Supported Platforms

| Platform | Architecture | OS |
|----------|-------------|-----|
| Apple Silicon | M1-M4 | macOS |
| Intel | x86_64 | Ubuntu |
| IBM Power | Power9 | RedHat |

**Python versions:** 3.10 - 3.12

## Installation

### Basic Installation

```bash
pip install QStone
```

### Full Installation with MPI Support

First, install OpenMPI:

```bash
# Ubuntu/Debian
sudo apt install openmpi-bin openmpi-common libopenmpi-dev

# RedHat/CentOS/Fedora  
sudo yum install openmpi openmpi-devel

# macOS
brew install openmpi
```

Then install QStone with MPI support:

```bash
pip install QStone[mpi]
```

## Usage

### 1. Generate Benchmark Suite

```bash
qstone generate -i config.json [--atomic/-a] [--scheduler/-s "slurm"/"jsrun"/"bare_metal"]
```

**Options:**
- `--atomic` / `-a`: Generate single-step jobs instead of three-phase jobs (pre/run/post)
- `--scheduler` / `-s`: Select output scheduler (default: `bare_metal`)

**Supported schedulers:** bare metal, Altair/FNC, SLURM/SchedMD

### 2. Execute Benchmark

```bash
qstone run -i scheduler.qstone.tar.gz [-o output_folder]
```

**Alternative:** Extract the tar.gz file and run manually:
```bash
tar -xzf scheduler.qstone.tar.gz
cd qstone_suite
sh qstone.sh
```

### 3. Profile Results

**Single user:**
```bash
qstone profile --cfg config.json --folder qstone_profile
```

**Multiple users:**
```bash
qstone profile --cfg config.json --folder qstone_profile --folder qstone_profile2
```

## Configuration

### Sample Configuration File

Create a `config.json` file with the following structure:

```json
{
  "environment": { 
    "project_name": "my_quantum_project",
    "scheduling_mode": "LOCK",
    "job_count": 5,
    "qpu": {
      "mode": "RANDOM"
    },
    "connectivity": {
      "mode": "NO_LINK",
      "qpu": {
        "ip_address": "0.0.0.0",
        "port": 55
      }
    },
    "timeouts": {
      "http": 5,
      "lock": 4
    } 
  },
  "jobs": [
    {
      "type": "VQE",
      "qubits": [4, 6],
      "num_shots": [100, 200],
      "walltime": 10,
      "nthreads": 4,
      "app_logging_level": 2 
    },
    {
      "type": "RB",
      "qubits": [2],
      "num_shots": [100],
      "walltime": 10,
      "nthreads": 2
    },
    {
      "type": "QBC",
      "qubits": [4],
      "num_shots": [32],
      "walltime": 20,
      "nthreads": 2
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

For detailed configuration options, refer to the [JSON schema](qstone/utils/config_schema.py).

**Note:** Only SLURM currently supports the high-performance "SCHEDULER" mode with lowest latency. See [SLURM documentation](SLURM.md) for more details.

## Programmatic Usage

```python
from qstone.generators import generator

def main():
    generator.generate_suite(
        config="config.json",
        job_count=100, 
        output_folder=".", 
        atomic=False, 
        scheduler="bare_metal"
    )

if __name__ == "__main__":
    main()
```

## Supported Backend Connectivities

- **Local no-link runner** - For testing without quantum hardware
- **gRPC** - High-performance remote procedure calls
- **HTTP/REST** - Standard web-based communication
- **Rigetti** - Native Rigetti quantum computer integration

## Examples and Resources

- 📓 [Getting Started Notebook](examples/running/getting_started.ipynb)
- 🔧 [Adding New Computation Types](examples/adding/computation/README.md)
- 🌐 [Creating a Simple Gateway](examples/node/README.md)

## Contributing

- [Contributing Guidelines](contributing.md)
- [Change Log](changelog.md)

## License

[License](LICENSE)


---

*For questions, issues, or feature requests, please visit our [GitHub repository](https://github.com/your-org/qstone) or open an issue.*
