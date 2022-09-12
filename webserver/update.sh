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

# rebuild docker image
sudo docker build -t litai . --no-cache

# update database
sudo docker run litai -v ~/secrets:/secrets \
    python -m litai.db --append

# update scoring tables
for CONFIG_FILE in config/*; do
    sudo docker run litai \
        -v ~/secrets:/secrets \
        -v config:config \
        python -m litai.score $CONFIG_FILE
done
