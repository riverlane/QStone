"""Main file for qstone."""

import argparse
import logging
import os
import subprocess
from typing import Optional, Sequence

from qstone.generators import generator
from qstone.profiling import profile


def generate(args: Optional[Sequence[str]] = None) -> None:
    """Qstone cli subcommand for generator."""
    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Generating benchmark tarballs")

    # Adjusting job count
    job_count_s = args.job_count  # type: ignore[union-attr]
    if job_count_s is not None:
        job_count = int(job_count_s)
    else:
        job_count = None

    generated_files = generator.generate_suite(
        config=args.src,  # type: ignore[union-attr]
        job_count=job_count,  # type: ignore[arg-type]
        output_folder=args.dst,  # type: ignore[union-attr]
        atomic=args.atomic,  # type: ignore[union-attr]
        scheduler=args.scheduler,  # type: ignore[union-attr]
    )

    logger.info("Generated %s tar balls:", len(generated_files))
    logger.info("\n".join(generated_files))


def run(args: Optional[Sequence[str]] = None) -> None:
    """Qstone cli subcommand for executing scheduler."""
    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.dst:  # type: ignore[union-attr]
        destination = args.dst  # type: ignore[union-attr]
        os.makedirs(destination, exist_ok=True)
    else:
        destination = "."
    logger.info(
        ">>Extracting benchmark in %s", os.path.join(destination, "qstone_suite")
    )
    result = subprocess.run(
        ["tar", "-xvf", args.src, "-C", destination],  # type: ignore[union-attr]
        check=False,
        stdout=subprocess.DEVNULL,
    )
    logger.info(">>Starting benchmark... ")

    result = subprocess.run(
        ["sh", os.path.join(destination, "qstone_suite", "qstone.sh")], check=False
    )
    logger.info("Scheduler ran with status %s", result.returncode)


def prof(args: Optional[Sequence[str]] = None) -> None:
    """Qstone cli subcommand for profiling scheduler exection."""
    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Extracting scheduler tar file")
    # Folder can be a list of folders
    f = [args.folder] if isinstance(args.folder, str) else args.folder  # type: ignore[union-attr]
    profile.profile(args.cfg, f, args.pickle)  # type: ignore[union-attr]


def main(arg_strings: Optional[Sequence[str]] = None) -> None:
    """Qstone main entry point function.

    Args:
        arg_strings: Optionally manually provide argument strings (only used in tests).
    """
    parser = argparse.ArgumentParser(prog="qstone")

    subparsers = parser.add_subparsers(required=True)

    gen_cmd = subparsers.add_parser("generate", help="Generates job scheduler")

    gen_cmd.add_argument(
        "-i",
        "--src",
        help="Path to the input configuration",
        required=True,
        type=str,
    )

    gen_cmd.add_argument(
        "-o",
        "--dst",
        help="Path to the folder where the schedulers will be generated ",
        default=".",
        required=False,
        type=str,
    )

    gen_cmd.add_argument(
        "-n",
        "--job_count",
        help="Number of jobs to generate",
        default=None,
        required=False,
        type=str,
    )

    gen_cmd.add_argument(
        "-a",
        "--atomic",
        help="Generate a single job per application, default is three [pre,run,post]",
        default=False,
        required=False,
        action="store_true",
    )

    gen_cmd.add_argument(
        "-s",
        "--scheduler",
        help="Generate the configuration for a specific scheduler",
        default="bare_metal",
        choices=["slurm", "jsrun", "bare_metal"],
        required=False,
        type=str,
    )

    gen_cmd.set_defaults(func=generate)

    runner = subparsers.add_parser("run", help="Run scheduler")

    runner.add_argument(
        "-i",
        "--src",
        help="Path to scheduler tar file",
        required=True,
        type=str,
    )
    runner.add_argument(
        "-o",
        "--dst",
        help="Path to extract scheduler to ",
        required=False,
        type=str,
    )

    runner.set_defaults(func=run)

    profiler = subparsers.add_parser("profile", help="Profile job execution")

    profiler.add_argument(
        "--cfg", type=str, help="Configuration file used to generate the load"
    )
    profiler.add_argument(
        "--folder",
        type=str,
        action="append",
        help="Folder that contains the runs, repeatable argument",
    )
    profiler.add_argument(
        "--pickle",
        type=str,
        help="Optional Pickle filepath to store pickled dataframe",
        default="./QS_Profile.pkl",
    )

    profiler.set_defaults(func=prof)

    args = parser.parse_args(arg_strings)
    args.func(args)


if __name__ == "__main__":
    main()
