#!/usr/bin/env python3

import datetime
from functools import reduce
import logging
import os
import sqlite3
import sys
from typing import Dict, Iterable, Iterator, Tuple, Union

from slack import WebClient  # type: ignore
import yaml

logging.basicConfig(
    stream=sys.stdout, format="%(asctime)s :: %(levelname)s :: %(message)s"
)

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

try:
    with open(os.path.join(FILE_PATH, "config", "config.yaml")) as config_file:
        CONFIG = yaml.safe_load(config_file)
except FileNotFoundError:
    logging.error("Config file not found. Have you run install.py yet?")
    exit()

con = sqlite3.connect(os.path.join(FILE_PATH, "slack_track.db"), check_same_thread=False)
con.isolation_level = None
cursor = con.cursor()


def get_slack_users(slack_client: WebClient) -> list:
    all_users = slack_client.users_list()
    if all_users["ok"]:
        return all_users["members"]
    else:
        raise Exception("Unable to pull users list. Check your token and try again.")


def flatten_dict(multi_level: dict) -> dict:
    """
    Takes a single user dict and recursively pulls the keys and values, assembling them into a
    single-level deep dict.
    :param multi_level: dict from which you would like broken down to a single level deep
    :return: 1D dict
    """

    def reduction(d: dict, items: tuple):
        key, value = items
        if type(value) is dict:
            return reduce(reduction, value.items(), d)
        else:
            return {**d, **{key: value}}

    flat_dict: Dict[str, Union[int, float, str, bool]] = reduce(reduction, multi_level.items(), {})
    return flat_dict


def items_to_rows(users: list, column_names: tuple):
    today = datetime.date.today()

    def make_row(user: dict):
        flat = {**flatten_dict(user), **{"date": today}}
        row = [flat.get(x, None) for x in column_names]
        return row

    rows = map(make_row, users)
    return rows


def get_table_column_names(table: str) -> list:
    cursor.execute(f"PRAGMA table_info({table});")
    return [x[1] for x in cursor]


def get_only_valid_col_names(table: str, col_names: Iterable[str]) -> Iterator[str]:
    """
    Compares a group of column names against valid column names for that table as produced from the the
    SQLite PRAGMA table_info function for the specified table.
    :param table: The name of the table for which to check the column names.
    :param col_names: An iterable (list, set, tuple, etc.) from which you would like to check the validity against
                      the table's column names.
    :return: Filter for all of the matches.
    """
    table_cols = get_table_column_names(table)
    return filter(lambda x: x in table_cols, col_names)


def get_data_from_previous_run(*attrs) -> Iterator:
    """
    Retrieves the table data for the previous run from the db.
    :param attrs: The column name(s) to retrieve the data for (e.g. "name", "deleted", etc.). If not attrs are
                  specified, pulls all columns with "*".
    :return: Iterator of the sqlite cursor.
    """
    today = datetime.date.today()
    cursor.execute("SELECT DISTINCT date FROM Slack WHERE date != ?", (today,))
    sorted_dates = sorted(x[0] for x in cursor)
    if not sorted_dates:
        raise ValueError("Does not appear to have an data from a previous time.")
    else:
        selection = (
            "*" if not attrs else ",".join(get_only_valid_col_names("Slack", attrs))
        )
        if not selection:
            raise ValueError(
                "No valid column names specified. To get all columns, leave argument empty"
            )
        else:
            cursor.execute(
                f"SELECT {selection} FROM Slack WHERE date = ?", (sorted_dates[-1],)
            )
            return (x for x in cursor)


def compare_current_and_previous_datasets(*attrs) -> Tuple[set, set]:
    """
    Compares the previous two runs (where the most recent is usually the "current" run) of the script. Does the
    comparison by utilizing the set.differences of the two. This works well when comparing a few attributes, such as
    name and deleted, but doesn't work well when comparing all columns.
    :param attrs: The column names to compare between the two runs (e.g. "name", "deleted", etc.). If no attrs are
                  specified, pulls all columns with "*".
    :return: Tuple of the set differences, with 0 being difference between current and previous, and 1 being difference
             between previous and current. See: set.difference() documentation for an explanation.
    """
    selection = "*" if not attrs else ",".join(get_only_valid_col_names("Slack", attrs))
    cursor.execute(
        f"SELECT {selection} FROM Slack WHERE date = ?", (datetime.date.today(),)
    )
    todays_data = set(cursor)
    previous_data = set(get_data_from_previous_run(*attrs))
    return (
        todays_data.difference(previous_data),
        previous_data.difference(todays_data),
    )


def get_users_created_and_deleted_since_last_run() -> str:
    """
    Mainly just a demo function. Outputs a string with three groups: new users, users whose accounts have been
    deactivated since the last run, and users whose accounts have been reactivated since the last run.
    """
    first_group, second_group = compare_current_and_previous_datasets("name", "deleted")
    fg_dict = {x[0]: x[1] for x in first_group}
    sg_dict = {x[0]: x[1] for x in second_group}
    first_group_users = set(fg_dict.keys())
    second_group_users = set(sg_dict.keys())
    new_users = first_group_users.difference(second_group_users)
    changed_status_users = second_group_users.difference(new_users)
    reactivated_users = {x for x in changed_status_users if sg_dict[x] == 1}
    deleted_users = {x for x in changed_status_users if sg_dict[x] == 0}
    output = (
            "New Users:\n" +
            '\n'.join(new_users) +
            "\n\n\nDeleted Users:\n" +
            '\n'.join(deleted_users) +
            "\n\n\nReactivated Users:\n" +
            "\n".join(reactivated_users))
    return output


def main():
    print("Starting up.")
    slack_client = WebClient(token=CONFIG["slack_token"])
    slack_users = get_slack_users(slack_client)
    column_names = tuple(["date"] + list(flatten_dict(slack_users[0]).keys()))
    cursor.execute(f"CREATE TABLE IF NOT EXISTS Slack {column_names}")
    rows = items_to_rows(slack_users, column_names)
    question_marks = ",".join("?" for _ in range(len(column_names)))
    col_name_strings = ",".join(str(x) for x in column_names)
    cursor.executemany(
        f"INSERT INTO Slack ({col_name_strings}) VALUES ({question_marks})", rows
    )
    con.commit()


if __name__ == "__main__":
    main()
