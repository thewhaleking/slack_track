#!/bin/bash

SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [ ! -d "$SCRIPT_PATH/venv" ];
  then python3 -m venv "$SCRIPT_PATH/venv";
fi;
PY="$SCRIPT_PATH/venv/bin/python";
"$PY" -m ensurepip;
"$PY" -m pip install -U pip;
"$PY" -m pip install -r requirements.txt;
"$PY" install.py;

