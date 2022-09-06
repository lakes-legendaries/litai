#!/bin/bash

# exit on error
set -e

# remove existing docker containers
CONTAINERS="$(docker ps -q)"
if [ ! -z "$CONTAINERS" ]; then
    docker rm --force "$CONTAINERS"
fi

# create temporary dockerfile
head -16 Dockerfile > Dockerfile.tmp
echo 'CMD [ "uvicorn", "litai.app:app", "--host", "0.0.0.0", "--port", "80" ]' >> Dockerfile.tmp

# rebuild docker image
docker build -t litai . -f Dockerfile.tmp

# remove temp dockerfile
rm Dockerfile.tmp

# start api service
docker run -dp 80:80 -v ~/secrets:/secrets litai
