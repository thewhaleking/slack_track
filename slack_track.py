#!/usr/bin/env python3

import datetime
from functools import reduce
import logging
import os
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


def main():
    slack_client = WebClient(token=CONFIG["slack_token"])
    slack_users = get_slack_users(slack_client)
    keys = flatten_keys(slack_users[0])
    print(keys)


if __name__ == "__main__":
    main()

