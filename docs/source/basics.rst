Basics
======

QStone generates sets of synthetic benchmarks that can be run on different architectures/with different schedulers.

It can be used to investigate few simple metrics:
- average compute times (quantum/classical computations)
- total run times

Average compute times
~~~~~~~~~~~~~~~~~~~~~

QStone can be leveraged to investigated where the hybrid quantum/classical computations spend their time. 

To start with a simple example, generate a simple configuration copy the file `latencies small <https://github.com/riverlane/QStone/tree/main/tests/data/generator/config_single.json>`_ and
modify the values for the `qpu_ip_address`, `qpu_port` and `project_name` (if your organisation requires jobs to be executed under specific user-groups/projects).
Then call the generate step:

.. code-block:: bash

    qstone generate -i config_single.json -s "bare_metal"   

QStone will generate a bare-metal job, i.e. a job that does not use scheduling to run one after the other 100 jobs. To actually execute the jobs, simply call:

.. code-block:: bash
   
    qstone run -i bare_metal_user0.qstone.tar.gz -o run_user0   

The jobs (only for a single user in this case) will now start and execute one after the other. 

From this first run, running the profiler could already highlight some interesting aspects of the HPC/Quantum system. To run the profiler execute:

.. code-block:: bash
    
   qstone profile --cfg config_single.json --folder run_user0/qstone_suite/qstone_profile  

that will return the overall execution time, the average execution time on the QPU and on the classical resources. This information can be already useful to understand the average computation duration for standard operations. 
