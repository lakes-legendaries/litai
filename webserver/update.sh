#!/bin/bash

# exit on error
set -e

# update litai code
cd /home/mike/litai
git pull origin main

# rebuild docker image
sudo docker build -t litai .

# update pubmed database
cmd/get-files
sudo docker run --rm -v $(pwd)/data:/code/data litai \
    python litai/db.py --append

# update scoring tables
for TABLE in covid hbot senescence; do
    sudo docker run \
        --rm \
        -v $(pwd)/data:/code/data \
        -v $(pwd)/config:/code/config \
        litai \
        python litai/score.py config/$TABLE.yaml
done

# upload db and website
export AZURE_STORAGE_CONNECTION_STRING="$(cat /home/mike/secrets/litai-fileserver)"
az storage blob upload -f data/pubmed.db -c data -n pubmed.db --overwrite
az storage blob upload-batch -s html/ -d \$web --overwrite

# restart api
/home/mike/litai/webserver/startup.sh
