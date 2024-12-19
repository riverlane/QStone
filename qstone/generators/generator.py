"""
Generation of the testbench.
"""

import argparse
import os
import shutil
import tarfile
from typing import List

import numpy
import pandas as pd
from jinja2 import Template

from qstone.utils.utils import (
    JOB_SCHEMA,
    USER_SCHEMA,
    QpuConfiguration,
    get_config_environ_vars,
    load_jobs,
    load_users,
)

SCHEDULERS = {
    "bare_metal": "bare_metal",
    "jsrun": "lsf/jsrun",
    "slurm": "slurm/schedmd",
}
SCHEDULER_CMDS = {"bare_metal": "bash", "jsrun": "jrun", "slurm": "sbatch"}
SCHEDULER_EXTS = {"bare_metal": "sh", "jsrun": "bsub", "slurm": "sbatch"}

SCHEDULER_ARGS = {"walltime": "3", "nthreads": "1"}

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
GEN_PATH = "qstone_suite"


def _get_value(job_cfg: pd.DataFrame, key: str, default: str):
    val = default
    try:
        val = job_cfg[key].values[0]
    except (KeyError, IndexError):
        pass
    if val is numpy.nan:
        val = default
    return str(val)


def _render_templates(
    sched: str, sched_path: str, subs: dict, job_types: List[str], jobs_cfg: dict
):
    """Convert all templates and add all the files that are in the scheduler folder"""
    # Add common folder here
    search_paths = [sched_path, os.path.join(CURRENT_PATH, "common")]

    # Ignore folders and search in the search paths all the paths
    all_files = [
        os.path.join(search_path, s)
        for search_path in search_paths
        for s in os.listdir(search_path)
        if s not in ["__pycache__", ".cache"] and not s.endswith(".pyc")
    ]
    jinja_files = [s for s in all_files if s.endswith("jinja")]
    non_jinja_files = list(set(all_files) - set(jinja_files))
    # Adding templated files
    for jinja_file in jinja_files:
        with open(jinja_file, encoding="utf-8") as fid:
            source = fid.read()
        if "{app}" in jinja_file:
            for t in job_types:
                outfile = os.path.join(
                    GEN_PATH,
                    os.path.basename(
                        jinja_file.replace(".jinja", "").replace("{app}", t)
                    ),
                )
                j = jobs_cfg[jobs_cfg["type"] == t]
                args = {
                    key: _get_value(j, key, val) for key, val in SCHEDULER_ARGS.items()
                }
                sched_args = {"sched_args": _get_value(j, f"{sched}_opt", "")}
                Template(source).stream({**subs, **args, **sched_args}).dump(outfile)
        else:
            outfile = os.path.join(
                GEN_PATH, os.path.basename(jinja_file.replace(".jinja", ""))
            )
            Template(source).stream(subs).dump(outfile)
    # Adding non template files
    for non_jinja_file in non_jinja_files:
        shutil.copy(
            non_jinja_file,
            f"{os.path.join(GEN_PATH, os.path.basename(non_jinja_file))}",
        )


def _render_and_pack(
    scheduler: str,
    output_filename: str,
    subs: dict,
    job_types: List[str],
    jobs_cfg: dict,
):
    """
    Renders and packs all the necessary files to run as a user
    """
    sched = SCHEDULERS[scheduler]
    sched_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), sched)
    shutil.rmtree(GEN_PATH, ignore_errors=True)
    os.makedirs(GEN_PATH)
    _render_templates(sched, sched_path, subs, job_types, jobs_cfg)
    # Copy the required files.
    with tarfile.open(output_filename, "w:gz") as tar:
        # Adding necessary scripts excluding original templates
        tar.add(GEN_PATH, recursive=True)
        for job_type in job_types:
            # Adding user defined apps
            job_cfg = jobs_cfg[jobs_cfg["type"] == job_type]
            app = _get_value(job_cfg, "path", "")
            if app:
                assert os.path.exists(app)
                tar.add(
                    app,
                    arcname=f"{GEN_PATH}/{os.path.basename(app)}",
                    recursive=False,
                )
    shutil.rmtree(GEN_PATH)


def _compute_job_pdf(usr_cfg: dict) -> List[float]:
    """Computes the normalized pdf to assign to different jobs based on user
    configurations and speciified qubit capacity
    """

    pdf = [prob for comp, prob in usr_cfg["computations"].items()]

    normalized = [float(p) / sum(pdf) for p in pdf]

    return normalized


def _generate_user_jobs(
    usr_cfg: dict, jobs_cfg: dict, job_pdf: List[float], num_calls: int
):
    """
    Generates the different user jobs provided given the configuration and the number of
    calls.
    """
    runner = 'python "$EXEC_PATH"/type_exec.py'
    job_types = numpy.random.choice(
        list(usr_cfg["computations"].keys()), p=job_pdf, size=(num_calls)
    )
    # Check that we have generated a not empty
    assert (
        len(job_types) > 0
    ), "Configuration generated zero jobs. Please check your configuration file."

    # Randomise number of qubits
    num_qubits = []
    num_shots = []
    for j in job_types:
        app_cfg = jobs_cfg[jobs_cfg["type"] == j]
        num_qubits.extend(
            numpy.random.randint(app_cfg["qubit_min"], app_cfg["qubit_max"])
        )
        num_shots.extend(
            numpy.random.randint(app_cfg["num_shots_min"], app_cfg["num_shots_max"])
        )

    # Assign job id and pack
    job_ids = list(range(len(job_types)))

    return (
        list(zip([f"{runner} {s}" for s in job_types], num_qubits, job_ids, num_shots)),
        set(job_types),
    )


def _environment_variables_exports(env_vars: dict) -> List[str]:
    """
    Generates export statements for environment variables.
    """
    exports_list = [
        f'export {k.upper().replace(".","_")}="{v}"' for k, v in env_vars.items()
    ]

    return exports_list


def generate_suite(
    config: str, num_calls: int, output_folder: str, atomic: bool, scheduler: str
) -> List[str]:
    """
    Generates the suites of jobs for the required users.

    Args:
        config: Input configuration for generate, defines QPU configuration and user jobs
        num_calls: Number of jobs to generate per user
        output_folder: Scheduler tar file output location
        atomic: optional flag to create a single job out of the three phase
        scheduler: target HPC scheduler

    Returns list of output file paths
    """
    users_cfg = load_users(config, USER_SCHEMA)
    jobs_cfg = load_jobs(config, JOB_SCHEMA)
    env_vars = get_config_environ_vars(config)
    env_exports = _environment_variables_exports(env_vars)

    qpu_config = QpuConfiguration()
    qpu_config.load_configuration(get_config_environ_vars(config))

    # Generating list of jobs
    output_paths = []
    for prog_id, user_cfg in users_cfg.iterrows():
        pdf = _compute_job_pdf(user_cfg)
        jobs, job_types = _generate_user_jobs(
            user_cfg, jobs_cfg, pdf, int(user_cfg["weight"] * num_calls)
        )

        # generate substitutions for Jinja templates
        formatted_jobs = [" ".join(map(str, job)) for job in jobs]

        user_name = user_cfg["user"]
        usr_env_exports = [
            f'export PROG_ID="{prog_id}"',
            f'export QS_USER="{user_name}"',
        ]
        subs = {
            "exports": "\n".join(env_exports + usr_env_exports),
            "jobs": "\n".join(formatted_jobs),
            "project_name": env_vars["project_name"],
            "atomic": atomic,
            "sched_ext": SCHEDULER_EXTS[scheduler],
            "sched_cmd": SCHEDULER_CMDS[scheduler],
        }
        # Pack project files
        filename = os.path.join(output_folder, f"{scheduler}_{user_name}.qstone.tar.gz")
        # render and pack all the files
        _render_and_pack(scheduler, filename, subs, job_types, jobs_cfg)
        output_paths.append(filename)
    return output_paths


def main():
    """
    Runs the generator phase.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str)
    parser.add_argument("num_calls", type=int)
    parser.add_argument("output_folder", type=str)
    parser.add_argument("scheduler", type=str, choices=SCHEDULERS)
    parser.add_argument("atomic", type=bool, action="store_true")
    args = parser.parse_args()
    generate_suite(
        args.config, args.num_calls, args.output_folder, args.atomic, args.scheduler
    )


if __name__ == "__main__":
    main()
