# Configuration file

This page describes the format of the configuration file.

```json
{
  "project_name": "proj_name",  // The name of the project. Becomes the resource group used by the scheduler.
  "connector": "NO_LINK",       // Type of connector. Options are NO_LINK, HTTP, GRPC
  "qpu_ip_address": "0.0.0.0",  // The address of the QPU (or associated gateway PC). Used in HTTP and GRPC mode.
  "qpu_port": "55",             // The port number of the QPU. Used in HTTP mode.
  "qpu_management": "LOCK",     // [Optional] Type of sharing mechanism. If scheduler does not support quantum resources jobs can either 
                                // query (QUERY) the remote resource or lock (LOCK) via a local file. If it does, leave it empty or set it to "NONE" 
  "lock_file": "path_to_the_lock", // [Optional] Path to the lockfile. Use when qpu_management == "LOCK". If not specified default is "qstone.lock".
  "timeouts": {
    "http": 3,  // Time before failing the http response
    "lock": 10, // Time before failing to acquire the lock
  }
  "jobs": [                     // Jobs definition
    { 
      "type": "VQE",            // The type of app. Applications can be from the core library or defined by the user.
      "num_shots": 100,         // Number of shots per run. Some applications might ignore the value.
      "qubit_min": 2,           // When randomising the number of qubits, this will be the lowest value 
      "qubit_max": 4,           // When randomising the number of qubits, this will be the highest value
      "walltime" : 10,          // Option to define a maximum execution time (timeout) to pass the scheduler for this specific app.
      "nthreads" : 4,           // Number of threads required.
      "lsf/jsrun_opt": "-nnodes=4 " // [Optional] Custom options to the scheduler. Format is "lsf/jsrun_opt" or ""slurm/schedmd_opt followed by the option. 
                                    // The option is passed to the scheduler directly e.g. jsrun -nnodes=4 python3 type_exec.py VQE 2 2 
    },
  ],

  "users": [                    // Users configuration 
    {
      "user": "user0",          // User name 
      "weight": 1,              //  
      "computations": {         // Distribution of the different applications in the final benchmarking script.
        "VQE": 0.05,
        "RB": 0.94,
        "PyMatching": 0.01
      }
    }
  ]
}
```



