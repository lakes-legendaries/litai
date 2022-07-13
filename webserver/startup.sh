#!/bin/bash

# exit on error
set -e

# renew certificates, copy into secrets
sudo certbot renew
for FILE in \
    /etc/letsencrypt/live/litai.eastus.cloudapp.azure.com/fullchain.pem \
    /etc/letsencrypt/live/litai.eastus.cloudapp.azure.com/privkey.pem \
; do
    sudo cp $FILE ~/secrets/
done

# remove unused docker images and containers
CONTAINERS="$(sudo docker ps -q)"
if [ ! -z "$CONTAINERS" ]; then
    sudo docker rm --force "$CONTAINERS"
fi
sudo docker system prune --force --all

# build docker image, start api service
cd /home/mike/litai
sudo docker build -t litai .
sudo docker run -dp 443:443 -v ~/secrets:/secrets -v $(pwd)/data:/code/data litai
