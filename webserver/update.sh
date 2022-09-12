#!/bin/bash

# exit on error
set -e

# run in project root
cd $(realpath $(dirname $BASH_SOURCE))/..

# check if updates are paused
if [ -f pause-updates ]; then
    exit 0
fi

# update code
git checkout main
git pull origin main

# update database
.venv/bin/python litai/db.py --append 

# update scoring tables
for CONFIG_FILE in config/*; do
    .venv/bin/python litai/score.py $CONFIG_FILE
done
