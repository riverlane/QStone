.. _slurm-label:

SLURM
=====

SLURM allows the definition of custom resources (generalised resources) that the scheduler uses to handle job scheduling and execution.
One possible way to introduce the concept of Quantum Computers as a shared resource requires three steps:

1. As administrator include a `gres.conf` file in the Slurm configuration folder. In this file define the quantum computer resource. A possible implementation:

.. code::
 
	# Configure 1 QPUs. The scheduler can only decrement (or restore) the resource counter
	NodeName=my-worker Name=qpu Count=1 Flags=CountOnly


2. Modify the `slurm.conf` file to include the GRES resources. Append at the end of the file the entry `Gres=qpu:1` previsiously defined in the `gres.conf`. 
Note: the name of the workers must match.

.. code::

	# Server configuration
	GresTypes=qpu
	NodeName=my-worker Gres=qpu:1 CPUs=108 Sockets=1 CoresPerSocket=108 RealMemory=32000 NodeAddr=127.0.0.1 State=UNKNOWN
	PartitionName=RL1 Nodes=my-worker Default=YES MaxTime=INFINITE State=UP
 
3. QStone can now be told to generate a benchmark in which the SLURM runner leverages the GRES=qpu during the phase of active engangement with the QPU by setting 
qpu_management=SCHEDULER in the `config.json` file. This will add the request to use a gres=qpu into the srun call.
 
