import os
import yaml

ABS_ROOT = os.path.abspath(os.path.dirname(__file__))

CONFIG_DIR = os.path.join(ABS_ROOT, "config")
with open(os.path.join(CONFIG_DIR, "config.yml")) as conf_file:
    CONFIG = yaml.safe_load(conf_file)
