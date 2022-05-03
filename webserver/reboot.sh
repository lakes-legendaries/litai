#!/bin/bash

# exit on error
set -e

# enter working directory
cd /home/$USER/litai

# activate virtual environment
source .venv/bin/activate
export PYTHONPATH=$(pwd)

# run app
KEYDIR=/etc/letsencrypt/live/litai.eastus.cloudapp.azure.com
uvicorn litai.app:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile=$KEYDIR/privkey.pem \
    --ssl-certfile=$KEYDIR/fullchain.pem \
