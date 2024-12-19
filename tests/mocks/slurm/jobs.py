import os
from pathlib import Path

import click


@click.group()
def cli():
    pass


@cli.command()
def pre_type0():
    Path(f'{os.environ["OUTPUT_PATH"]}/pre_type0').touch()


@cli.command()
def run_type0():
    Path(f'{os.environ["OUTPUT_PATH"]}/run_type0').touch()


@cli.command()
def pre_type1():
    Path(f'{os.environ["OUTPUT_PATH"]}/pre_type1').touch()


@cli.command()
def run_type1():
    Path(f'{os.environ["OUTPUT_PATH"]}/run_type1').touch()


@cli.command()
def post_type1():
    Path(f'{os.environ["OUTPUT_PATH"]}/post_type1').touch()


@cli.command()
def pre_type2():
    Path(f'{os.environ["OUTPUT_PATH"]}/pre_type2').touch()


@cli.command()
def run_type2():
    Path(f'{os.environ["OUTPUT_PATH"]}/run_type2').touch()


@cli.command()
def post_type2():
    Path(f'{os.environ["OUTPUT_PATH"]}/post_type2').touch()


if __name__ == "__main__":
    cli()
