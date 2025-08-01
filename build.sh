#!/usr/bin/env bash
# Tell Render to use Python 3.10
echo "python-3.10" > runtime.txt
pip install --upgrade pip
pip install -r requirements.txt
