#!/bin/bash

# exit on error
set -e

# run in project root
cd $(realpath $(dirname $BASH_SOURCE))/..

# renew certificates, copy into secrets
sudo certbot renew
for FILE in \
    /etc/letsencrypt/live/litai.eastus.cloudapp.azure.com/fullchain.pem \
    /etc/letsencrypt/live/litai.eastus.cloudapp.azure.com/privkey.pem \
; do
    sudo cp $FILE ~/secrets/
done

# remove existing docker containers and images
CONTAINERS="$(sudo docker ps -q --filter publish=443)"
if [ ! -z "$CONTAINERS" ]; then
    sudo docker rm --force "$CONTAINERS"
fi
sudo docker system prune --force --all

# rebuild docker image
sudo docker build -t litai . --no-cache

# start api service
sudo docker run -dp 443:443 -v ~/secrets:/secrets litai
