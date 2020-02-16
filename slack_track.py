#!/usr/bin/env python3

import datetime
from functools import reduce
import logging
import os
import sqlite3
import sys
from typing import List, Tuple

from slack import WebClient
import yaml

logging.basicConfig(
    stream=sys.stdout, format="%(asctime)s :: %(levelname)s :: %(message)s"
)

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

try:
    with open(os.path.join(FILE_PATH, "config", "config.yaml")) as config_file:
        CONFIG = yaml.safe_load(config_file)
except FileNotFoundError:
    logging.error("Config file not found. Have you run setup.py yet?")
    exit()

con = sqlite3.connect("slack_track.db", check_same_thread=False)
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

    flat_dict = reduce(reduction, multi_level.items(), {})
    return flat_dict


def items_to_rows(users: list, column_names: tuple):
    indices = {y: x for (x, y) in enumerate(column_names)}
    num_of_cols = len(column_names)
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


def get_only_valid_col_names(table: str, col_names: list) -> iter:
    table_cols = get_table_column_names("Slack")
    return filter(lambda x: x in table_cols, col_names)


def get_data_from_previous_run(*attrs) -> iter:
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
                "No valid column names specified. To get all columnds, leave argument empty"
            )
        else:
            cursor.execute(
                f"SELECT {selection} FROM Slack WHERE date = ?", (sorted_dates[-1],)
            )
            return (x for x in cursor)


def compare_current_and_previous_datasets(*attrs) -> List[tuple]:
    table_cols = get_table_column_names("Slack")
    selection = "*" if not attrs else ",".join(get_only_valid_col_names("Slack", attrs))
    cursor.execute(
        f"SELECT {selection} FROM Slack WHERE date = ?", (datetime.date.today(),)
    )
    todays_data = set(cursor)
    previous_data = set(get_data_from_previous_run(*attrs))
    return [
        todays_data.difference(previous_data),
        previous_data.difference(todays_data),
    ]


def get_users_deleted_since_last_run():
    """
    Mainly just a demo function. Gives the users that have had their deleted status changed since
    the last run. This should also give reactivated users.
    """
    comparison = compare_current_and_previous_datasets("name", "deleted")
    return comparison[0] + comparison[1]


def main():
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
