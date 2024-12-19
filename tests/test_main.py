""" Tests for qstone cli"""

from unittest.mock import patch

import pytest

from qstone.__main__ import main


def test_arg_parse():
    """Check exits without SRC"""
    with patch("qstone.__main__.argparse.ArgumentParser") as exit_mock:
        exit_mock.side_effect = TypeError
        with pytest.raises(TypeError):
            main([])
        exit_mock.assert_called_once()


def test_cmd_generate():
    """Test that arguments are provided to qstone generate correctly."""
    input_path = "path/to/input_path"
    output = "path/to/output"
    num_calls = 0

    # Check generate command
    with patch("qstone.generators.generator.generate_suite") as generate_qstone:
        main(["generate", "-i", input_path, "-n", num_calls, "-o", output])
        generate_qstone.assert_called_once_with(
            config=input_path,
            num_calls=num_calls,
            output_folder=output,
            atomic=False,
            scheduler="bare_metal",
        )


def test_cmd_run(tmp_path):
    """Test that arguments are provided to qstone run correctly."""
    input_path = "path/to/input_path"

    # Check generate command
    with patch("subprocess.run") as run_subprocess:
        main(["run", "-i", "input_path", "-o", str(tmp_path)])
        run_subprocess.assert_called()


def test_cmd_profile():
    """Test that arguments are provided to profile profile correctly."""
    input_path = "path/to/input_path"
    output = "path/to/output"

    # Check generate command
    with patch("qstone.profiling.profile.profile") as profile_qstone:
        main(["profile", "--cfg", input_path, "--folder", output])
        profile_qstone.assert_called_once_with(input_path, [output], "./QS_Profile.pkl")
