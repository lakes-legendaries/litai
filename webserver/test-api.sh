#!/bin/bash

# exit on error
set -e

# run in project root
cd $(realpath $(dirname $BASH_SOURCE))/..

# remove existing docker containers
CONTAINERS="$(sudo docker ps -q --filter publish=1024)"
if [ ! -z "$CONTAINERS" ]; then
    sudo docker rm --force "$CONTAINERS"
fi

# rebuild docker image
sudo docker build -t litai-dev . -f Dockerfile.dev

# start api service
sudo docker run -dp 1024:443 -v ~/secrets:/secrets litai-dev
