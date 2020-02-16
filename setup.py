#!/usr/bin/env python3

import os
import shutil
import subprocess

import yaml

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def main():
    config_yaml = os.path.join(FILE_PATH, "config", "config.yaml")
    if not os.path.exists(config_yaml):
        config_template = os.path.join(FILE_PATH, "config", "config.yaml.tpl")
        shutil.copyfile(config_template, config_yaml)
    with open(config_yaml) as config_file:
        config = yaml.safe_load(config_file)
    if not config.get("slack_token"):
        slack_token = input("Please enter/paste your slack token here")
        config.update({"slack_token": slack_token})
    with open(config_yaml, "w") as config_file:
        yaml.dump(config, config_file)
    frequencies = (
        "yearly",
        "monthly",
        "weekly",
        "daily",
        "manually (to not run automatically)",
    )

    def get_frequency() -> str:
        print("How often would you like the script to run?")
        print(f"You can specify: {', '.join(frequencies)}")
        freq = input().strip()
        if freq != "manually" and freq not in frequencies:
            return get_frequency()
        else:
            return freq

    desired_frequency = get_frequency()
    if desired_frequency != "manually":
        python_bin = os.path.join(FILE_PATH, "venv", "bin", "python")
        script_path = os.path.join(FILE_PATH, "slack_track.py")
        user = os.environ["USER"]
        subprocess.call(
            f"""(crontab -l; echo "@{desired_frequency} {python_bin} {script_path}" )"""
            f"""| crontab -""",
            shell=True,
        )


if __name__ == "__main__":
    main()
