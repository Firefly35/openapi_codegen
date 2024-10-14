#!/bin/bash

python3 -m venv openapigen_env && source openapigen_env/bin/activate
# For python pgsql
pip install --upgrade pip
pip install --upgrade jsonpath-ng