#!/bin/bash

# alias directories
KEYDIR=/etc/letsencrypt/live/litai.eastus.cloudapp.azure.com
LITDIR=/home/mike/litai

# stop running services
sudo kill -9 $(ps -A | grep python | awk '{print $1}')

# run in litai dir
cd $LITDIR

# run app
sudo PYTHONPATH=$LITDIR $LITDIR/.venv/bin/python \
    -m uvicorn litai.app:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile=$KEYDIR/privkey.pem \
    --ssl-certfile=$KEYDIR/fullchain.pem \
