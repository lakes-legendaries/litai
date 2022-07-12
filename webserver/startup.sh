#!/bin/bash

# exit on error
set -e

# renew certificates
sudo certbot renew

# remove unused docker images and containers
CONTAINERS="$(sudo docker ps -q)"
if [ ! -z "$CONTAINERS" ]; then
    sudo docker rm --force "$CONTAINERS"
fi
sudo docker system prune --force --all

# clone repo
rm -rfd litai
git clone https://github.com/lakes-legendaries/litai.git

# download database
export AZURE_STORAGE_CONNECTION_STRING="$(cat /home/mike/secrets/litai-fileserver)"
az storage blob download -f litai/data/pubmed.db -c data -n pubmed.db

# copy certs into secrets
for FILE in \
    /etc/letsencrypt/live/litai.eastus.cloudapp.azure.com/fullchain.pem \
    /etc/letsencrypt/live/litai.eastus.cloudapp.azure.com/privkey.pem \
; do
    sudo cp $FILE ~/secrets/
done

# build docker image
cd litai
sudo docker build -t litai .

# run docker container
sudo docker run -dp 443:443 -v ~/secrets:/secrets -v $(pwd)/data:/code/data litai
