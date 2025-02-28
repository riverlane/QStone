"""Tests for scheduler and job generation"""

import importlib
import os
import shutil
import subprocess
import tarfile
import time

import pytest
from pytest_mock import mocker

import tests.mocks.lsf_jsrun.scheduler as jsrun_scheduler
from qstone.connectors.connector import ConnectorType
from qstone.generators import generator
from qstone.apps import PyMatching
from qstone.utils.utils import JobReturnCode, QpuConfiguration


SCHED_EXT = {"slurm": "sbatch", "jsrun": "bsub", "bare_metal": None}


@pytest.mark.parametrize("test_input", ["config_wrong_sum.json"])
def test_config_checks(tmp_path, test_input):
    with pytest.raises(Exception) as e_info:
        generator.generate_suite(
            config=f"tests/data/generator/{test_input}",
            num_calls=10000,
            output_folder=output_folder,
            atomic=atomic,
            scheduler=scheduler,
        )


@pytest.mark.parametrize(
    "test_input,expected,atomic,scheduler,use_gres",
    [
        ("config_single.json", ["user0"], False, "bare_metal", False),
        ("config_single_custom_app.json", ["user0"], False, "jsrun", False),
        ("config_multi.json", ["user0", "user1", "user2"], False, "slurm", False),
        ("config_single.json", ["user0"], True, "jsrun", False),
        ("config_single_scheduler.json", ["user0"], True, "slurm", True),
    ],
)
def test_packaging(tmp_path, test_input, expected, atomic, scheduler, use_gres):
    output_folder = tmp_path
    tmp_path.mkdir(exist_ok=True)
    generator.generate_suite(
        config=f"tests/data/generator/{test_input}",
        num_calls=10000,
        output_folder=output_folder,
        atomic=atomic,
        scheduler=scheduler,
    )
    for exp in expected:
        filename = os.path.join(tmp_path, f"{scheduler}_{exp}.qstone.tar.gz")
        assert os.path.isfile(filename)
        with tarfile.open(filename, "r:gz") as t:
            ext = SCHED_EXT[scheduler]
            if ext:
                keywords = [
                    "full" if atomic else "pre",
                    "--gres=qpu:1" if use_gres else "",
                ]
                content = str(t.extractfile(f"qstone_suite/type_exec_VQE.{ext}").read())
                assert all(x in content for x in keywords)


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("VQE_exec", ["pre_VQE", "run_VQE"]),
        ("RB_exec", ["pre_RB", "run_RB", "post_RB"]),
        ("PyMatching_exec", ["run_PyMatching", "post_PyMatching"]),
    ],
)
@pytest.mark.skipif(shutil.which("sbatch") == None, reason="Requires Slurm")
def test_slurm_runners(tmp_path, test_input, expected):
    tmp_path.mkdir(exist_ok=True)
    os.environ["RUNNER_PATH"] = "tests/mocks/slurm/"
    module = importlib.import_module(f"qstone.generators.slurm.schedmd.{test_input}")
    func = getattr(module, "execute")
    func()
    # Need to wait for slurm to schedule and run
    time.sleep(5)
    for f in expected:
        filepath = os.path.join(tmp_path, f)
        print(os.listdir(tmp_path))
        assert os.path.isfile(filepath)


@pytest.mark.parametrize(
    "test_input,usrs",
    [
        ("config_single.json", ["user0"]),
        ("config_single_custom_app.json", ["user0"]),
        ("config_multi.json", ["user0", "user1", "user2"]),
    ],
)
def test_bare_metal_run(tmp_path, test_input, usrs):
    """Test execution of bare metal basic job scheduler"""
    output_folder = tmp_path
    tmp_path.mkdir(exist_ok=True)
    generator.generate_suite(
        config=f"tests/data/generator/{test_input}",
        num_calls=5,
        output_folder=output_folder,
        atomic=False,
        scheduler="bare_metal",
    )
    for usr in usrs:
        sched = "bare_metal"
        filename = os.path.join(
            tmp_path, f'{sched.replace("/","_")}_{usr}.qstone.tar.gz'
        )
        assert os.path.isfile(filename)
        with tarfile.open(filename, "r|gz") as t:
            t.extractall(tmp_path)
        runner_path = os.path.join(tmp_path, "qstone_suite", "qstone.sh")
        result = subprocess.run(
            ["bash", runner_path],
            check=True,
        )
        assert result.returncode == 0


@pytest.mark.parametrize(
    "test_input,usrs",
    [
        ("config_single.json", ["user0"]),
    ],
)
def test_jsrun_batch_valid(tmp_path, test_input, usrs):
    """Test generated bsub batch script is valid."""
    scheduler = jsrun_scheduler.Scheduler()
    output_folder = tmp_path
    tmp_path.mkdir(exist_ok=True)
    generator.generate_suite(
        config=f"tests/data/generator/{test_input}",
        num_calls=20,
        output_folder=output_folder,
        atomic=False,
        scheduler="jsrun",
    )
    for usr in usrs:
        filename = os.path.join(tmp_path, f"jsrun_{usr}.qstone.tar.gz")
        assert os.path.isfile(filename)
        with tarfile.open(filename, "r|gz") as t:
            t.extractall(tmp_path)
        bsub_path = os.path.join(tmp_path, "qstone_suite", "type_exec_VQE.bsub")
        with open(bsub_path, encoding="utf-8") as bsub_file:
            bsub_script = bsub_file.read()
        assert "#BSUB -nnodes 2" in bsub_script
        assert "#BSUB -W 3" in bsub_script
        assert "jsrun -special_setting=True" in bsub_script

        assert scheduler.run(bsub_script)
