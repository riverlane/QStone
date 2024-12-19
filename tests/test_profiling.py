import os

import pandas as pd
import pytest

from qstone.profiling import profile


@pytest.fixture()
def sample_traced(tmp_path):
    """Fixture of sample trace information"""
    print(f"***********************")
    pickle = tmp_path / f"result.pkl"
    tmp_path.mkdir(exist_ok=True)
    profile.profile(
        config="tests/data/profiler/run1.json",
        folder=["tests/data/profiler/run1"],
        pickle=pickle,
    )


def test_profile(sample_traced, tmp_path):
    """Test profile runs and writes pickles sucessfully"""
    pickle = tmp_path / f"result.pkl"
    assert os.path.isfile(pickle)
    check = pd.read_pickle(pickle)
    assert "user1" in check["user"].unique()


def test_profile_loads_all_jsons(sample_traced, tmp_path):
    """Test profiler stores all tracer information"""
    pickle = tmp_path / f"result.pkl"
    df = pd.read_pickle(pickle)
    assert len(df) == len(os.listdir("tests/data/profiler/run1"))  # your directory path


def test_profiler_valid_schema(sample_traced, tmp_path):
    """Test generated hdf5 file is valid with the profiler schema"""
    pickle = tmp_path / f"result.pkl"
    df = pd.read_pickle(pickle)
    profile.PROFILER_SCHEMA.validate(df)
