#!/usr/bin/env python3

import datetime
from functools import reduce
import logging
import os
import sys

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
    return []


def main():
    slack_client = WebClient(token=CONFIG["slack_token"])
    slack_users = get_slack_users(slack_client)

if __name__ == "__main__":
    main()

