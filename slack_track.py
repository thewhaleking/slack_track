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


def items_to_rows(users: list, column_names: tuple):
    indices = {y: x for (x, y) in enumerate(column_names)}
    num_of_cols = len(column_names)

    def make_row(user: dict):
        row = ['' for _ in range(num_of_cols)]
        row[0] = datetime.date.today()

        def dict_breaker(d: dict):
            for key, value in d.items():
                if type(value) is dict:
                    return dict_breaker(value)
                else:
                    try:
                        row[indices[key]] = value
                    except KeyError:
                        pass
        dict_breaker(user)
        return row

    rows = map(make_row, users)
    return rows


def main():
    slack_client = WebClient(token=CONFIG["slack_token"])
    slack_users = get_slack_users(slack_client)
    column_names = tuple(["date"] + flatten_keys(slack_users[0]))
    try:
        cursor.execute(f"CREATE TABLE Slack {column_names}")
    except sqlite3.OperationalError:
        pass
    rows = items_to_rows(slack_users, column_names)
    question_marks = ','.join('?' for _ in range(len(column_names)))
    cursor.executemany(f"INSERT INTO Slack VALUES ({question_marks})", rows)
    con.commit()


if __name__ == "__main__":
    main()

