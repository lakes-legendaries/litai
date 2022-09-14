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
sudo docker run \
    -v ~/secrets:/secrets \
    --memory 4g \
    --cpus 1 \
    litai \
    python -m litai.db --append

# update scoring tables
sudo docker run \
    -v ~/secrets:/secrets \
    -v $(pwd)/config:/code/config \
    -v $(pwd)/data:/code/data \
    --memory 4g \
    --cpus 1 \
    litai \
    python -m litai.score

# restart service
webserver/run-service.sh
