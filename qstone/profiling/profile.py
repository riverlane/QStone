"""Profile utilities"""

import argparse
import logging
import os

import pandas as pd
import pandera.pandas as pa

from qstone.utils.utils import ComputationStep, load_json_profile, parse_json

PROFILER_SCHEMA = pa.DataFrameSchema(
    {
        "user": pa.Column(str),
        "prog_id": pa.Column(str),
        "job_id": pa.Column(str),
        "job_type": pa.Column(str),
        "job_step": pa.Column(
            str, checks=pa.Check.isin([e.name for e in ComputationStep])
        ),
        "start": pa.Column(int),
        "success": pa.Column(bool),
        "end": pa.Column(int),
    }
)


def _get_stats_from_dir(folder, schema):
    """
    Get the statistics from a folder applying the schema provided.
    """
    df = None
    for func_profile in os.listdir(folder):
        if func_profile.endswith(".json"):
            data = load_json_profile(os.path.join(folder, func_profile), schema)
            df = pd.concat([data, df], sort=False)
    logging.info("Folder: %s - found %d entries", folder, df.shape[0])
    return df


def _extrapolate(stats):
    """
    extrapolate provides an example of capabilities of Pandas.
    """
    # Adding an entry that defines the total duration
    stats["total"] = stats["end"] - stats["start"]
    # Aggregating micro-jobs with that belong to the same ID
    for pid in list(set(stats["prog_id"])):
        # Filtering per id
        mask = stats.prog_id == pid
        jobs = stats[stats.prog_id == pid]
        # We are aggregating all the steps associated with the same job
        for s in ["PRE", "RUN", "POST"]:
            stats.loc[mask, f"{s}_agg"] = jobs[jobs.job_step == s]["total"].sum()
    stats["count"] = len(stats[stats["success"]].groupby(["job_id", "user"]).groups)
    stats["connection_total"] = stats.query('job_type == "CONNECTION"')["total"].sum()
    return stats


def _store(stats, pickle):
    if os.path.exists(pickle):
        df = pd.concat([stats, pd.read_pickle(pickle)])
        df.to_pickle(pickle)
    else:
        stats.to_pickle(pickle)


NS_TO_MS = 1_000_000


def _print_stats(stats: pd.DataFrame):
    """
    Print general statistics
    """
    tot_classical = (stats["PRE_agg"].iloc[0] + stats["POST_agg"].iloc[0]) / NS_TO_MS
    tot_quantum = stats["RUN_agg"].iloc[0] / NS_TO_MS
    connection_total = stats["connection_total"].iloc[0] / NS_TO_MS
    tot_runs = stats["count"].iloc[0]
    print("########### Stats ######################")
    print(f"Total classical computation   [ms]:  {tot_classical:>12.2f}")
    print(f"Total quantum computation     [ms]:  {tot_quantum:>12.2f}")
    print(f"Average classical computation [ms]:  {tot_classical/tot_runs:>12.2f}")
    print(f"Average quantum computation   [ms]:  {tot_quantum/tot_runs:>12.2f}")
    print(f"Average connection time       [ms]:  {connection_total/tot_runs:>12.2f}")


def profile(
    config: str, folder: list[str], pickle: str
):  # pylint: disable=unused-argument
    """
    Profile the total execution across multiple users and store into
    a generalised pickled object.
    """
    # Get system configuration

    config_dict = parse_json(config)  # pylint: disable=unused-variable
    # Merging the results
    stats = pd.concat(
        [_get_stats_from_dir(f, PROFILER_SCHEMA) for f in folder], ignore_index=True
    )
    # Example of data extrapolation.
    _extrapolate(stats)
    # Store into an pickle file
    _store(stats, pickle)
    # Stats
    _print_stats(stats)


def main():
    """Main profile routine"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cfg", type=str, help="Configuration file used to generate the load"
    )
    parser.add_argument("folder", type=str, help="Folder that contains the runs")
    parser.add_argument(
        "--pickle", type=str, help="Optional Pickle filepath to store pickled dataframe"
    )
    args = parser.parse_args()
    profile(args.config, args.folder, args.pickle)


if __name__ == "__main__":
    main()
