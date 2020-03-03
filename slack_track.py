#!/usr/bin/env python3

import datetime
from functools import reduce
import logging
import os
import sys
from typing import Dict, List, Union, Iterator

from slack import WebClient  # type: ignore
import yaml

import reports
from utils.database_tools import DatabaseTools

logging.basicConfig(
    stream=sys.stdout, format="%(asctime)s :: %(levelname)s :: %(message)s"
)

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
FlatDict = Dict[str, Union[int, float, str, bool, list]]

try:
    with open(os.path.join(FILE_PATH, "config", "config.yaml")) as config_file:
        CONFIG = yaml.safe_load(config_file)
except FileNotFoundError:
    logging.error("Config file not found. Have you run install.py yet?")
    exit()


def get_slack_users(slack_client: WebClient) -> list:
    all_users = slack_client.users_list()
    if all_users["ok"]:
        return all_users["members"]
    else:
        raise Exception("Unable to pull users list. Check your token and try again.")


def flatten_dict(multi_level: dict) -> FlatDict:
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

    flat_dict: FlatDict = reduce(reduction, multi_level.items(), {})
    return flat_dict


def items_to_rows(users: List[dict], column_names: tuple) -> Iterator:
    today = datetime.date.today()

    def make_row(user: dict) -> list:
        flat = {**flatten_dict(user), **{"date": str(today)}}
        row = [flat.get(x, None) for x in column_names]
        return row

    rows = map(make_row, users)
    return rows


def main():
    print("Starting up.")
    slack_client = WebClient(token=CONFIG["slack_token"])
    slack_users = get_slack_users(slack_client)
    column_names = tuple(["date"] + list(flatten_dict(slack_users[0]).keys()))
    rows = items_to_rows(slack_users, column_names)
    question_marks = ",".join("?" for _ in range(len(column_names)))
    col_name_strings = ",".join(str(x) for x in column_names)
    db = DatabaseTools(os.path.join(FILE_PATH, "slack_track.db"), column_names)
    db.cursor.executemany(
        f"INSERT INTO Slack ({col_name_strings}) VALUES ({question_marks})", rows
    )
    db.con.commit()
    reports.main(db)


if __name__ == "__main__":
    main()
