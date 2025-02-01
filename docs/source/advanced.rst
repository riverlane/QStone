Advanced
========

QStone generates sets of synthetic benchmarks that can be run on different architectures/with different schedulers.

It can be used to extract more advanced indicators, normally of interest to HPC integrators:
- scheduling impact
- queueing time
- network time

Setup
~~~~~

Generate a configuration by copying the file `multi-user <https://github.com/riverlane/QStone/tree/main/examples/configs/advanced.json>`_ and
modify the values for the `qpu_ip_address`, `qpu_port` and `project_name` (if your organisation requires jobs to be executed under specific user-groups/projects).
Then call the generate step:

.. code-block:: bash

    qstone generate -i latencies_small.json -s "your_scheduler"   

QStone will generate 10 "your_scheduler" tar files that can be executed as 10 different users to simulate a realistic load. Once you have identified a sensible policy to execute as 10 different users (please note: only coarse synchronisation needed. Jobs are long enough that each user can start within seconds from the next with no significant effect on the metrics), call:

.. code-block:: bash
   
    qstone run -i your_scheduler_userx.qstone.tar.gz -o run_userx   

The jobs (only for a single user in this case) will now start and execute one after the other. 

Analysis
~~~~~~~~

From this first run, running the profiler could already highlight some interesting aspects of the HPC/Quantum system. To run the profiler execute:

.. code-block:: bash
    
   qstone profile --cfg latencies_small.json --folder run_user0 

that will return the overall execution time, the average execution time on the QPU and on the classical resources. This information can be already useful to understand the average computation duration for standard operations. 
