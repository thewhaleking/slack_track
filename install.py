#!/usr/bin/env python3

import os
import shutil
import subprocess

import yaml

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def main():
    config_yaml = os.path.join(FILE_PATH, "config", "config.yaml")
    if not os.path.exists(config_yaml):
        config_template = os.path.join(FILE_PATH, "config", "config.tpl.yaml")
        shutil.copyfile(config_template, config_yaml)
    with open(config_yaml) as config_file:
        config = yaml.safe_load(config_file)
    if not config.get("slack_token"):
        slack_token = input("Please enter/paste your slack token here")
        config.update({"slack_token": slack_token})
    with open(config_yaml, "w") as config_file:
        yaml.dump(config, config_file)
    frequencies = {
            "yearly": "0 0 1 1 *",
            "monthly": "0 0 1 * *",
            "weekly": "0 0 * * 0",
            "daily": "0 0 * * *",
            "manually (to not run automatically)": "",
        }

    def get_frequency() -> str:
        print("How often would you like the script to run?")
        print(f"You can specify: {', '.join(frequencies.keys())}")
        freq = input().strip()
        if freq != "manually" and freq not in frequencies.keys():
            return get_frequency()
        else:
            return freq

    desired_frequency = get_frequency()
    if desired_frequency != "manually":
        python_bin = os.path.join(FILE_PATH, "venv", "bin", "python")
        script_path = os.path.join(FILE_PATH, "slack_track.py")
        subprocess.call(
            f"""(crontab -l; echo "{frequencies[desired_frequency]} {python_bin} {script_path}" )"""
            f"""| crontab -""",
            shell=True
        )
    reports_fp = os.path.join(FILE_PATH, "reports.py")
    if not os.path.exists(reports_fp):
        shutil.copyfile(os.path.join(FILE_PATH, "reports.tpl.py"), reports_fp)


if __name__ == "__main__":
    main()
