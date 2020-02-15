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

logging.basicConfig(stream=sys.stdout, format="%(asctime)s :: %(levelname)s :: %(message)s")

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


def flatten_keys(user: dict) -> List[str]:
    """
    Takes a single user dict and recursively pulls the keys, concatenating them into a list.
    :param user: user dict from produced from the get_slack_users call
    :return: 1D list of the keys as strs
    """
    def reduction(keys: list, items: tuple):
        key, value = items
        if type(value) is dict:
            return reduce(reduction, value.items(), keys)
        else:
            return keys + [key]

    keys = reduce(reduction, user.items(), [])
    return list(keys)


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
        row = [flat.get(x, "") for x in column_names]
        return row

    rows = map(make_row, users)
    return rows


def get_table_column_names(table: str) -> list:
    cursor.execute(f"PRAGMA table_info({table});")
    return [x[1] for x in cursor]


def main():
    slack_client = WebClient(token=CONFIG["slack_token"])
    slack_users = get_slack_users(slack_client)
    column_names = tuple(["date"] + list(flatten_dict(slack_users[0]).keys()))
    cursor.execute(f"CREATE TABLE IF NOT EXISTS Slack {column_names}")
    rows = items_to_rows(slack_users, column_names)
    question_marks = ','.join('?' for _ in range(len(column_names)))
    col_name_strings = ','.join(str(x) for x in column_names)
    cursor.executemany(f"INSERT INTO Slack ({col_name_strings}) VALUES ({question_marks})", rows)
    con.commit()


if __name__ == "__main__":
    main()

