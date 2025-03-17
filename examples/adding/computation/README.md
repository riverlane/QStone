# Create new applications

### Adding a new application outside of the core library

1. Define your computation as in example_computation.py.
2. Modify the main json configuration file to include the application and provide a link to the local python file. 
3. In the configuration file define the job in "jobs" section providing the path to the python file in "path" and the "file.module" name in "type". The file will be added to the tar file that contains the executables. In the "users" section add the new application and assign a probability of executing it.

```json
{
  "environment": { 
     "project_name": "proj_name",
     ...   
  },
  "jobs": [
    {
      "type": "VQE",
      "qubit_min": 2,
      "qubit_max": 4,
      "walltime": 3,
      "nthreads": 2,
      "lsf/jsrun_opt": "-nnodes=4"
    },
    {
      "type": "custom1.Custom1",
      "path": "tests/data/apps/custom1.py",
      "qubit_min": 2,
      "qubit_max": 4,
      "walltime": 3,
      "nthreads": 2,
      "slurm/schedmd_opt": "--cpus-per-task=4" 
    }
  ],
  "users": [
    {
      "user": "user0",
      "weight": 1,
      "computations": {
        "VQE": 0.50,
        "custom1.Custom1" : 0.50
      }
    }
  ]
} 
```

### Adding a new application as part of the core library

1. Define your application as in example_computation.py. This is the src script of the application you want to run. Place this src in the qstone/apps folder.
2. Import your application's ApplicationClass in the qstone.apps' __init__.py file
3. In the same file, add "yourcomputationname" : ApplicationClass to the _computation_registry.
4. To use your computation simply use "yourcomputationname" when defining the configuration JSON for the generator. 
