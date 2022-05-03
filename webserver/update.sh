#!/bin/bash

# exit on error
set -e

# log console output to file
LOGS=/logs/update-databases-$(date +%F-%T).log
mkdir -p /logs
rm -f $LOGS
touch $LOGS
exec > $LOGS
exec 2>&1

# function to recreate venv
function new_venv () {
    rm -rfd .venv
    python3.9 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    export PYTHONPATH=$(pwd)
}

# renew certificates
sudo certbot renew
sudo chmod 777 -R /etc/letsencrypt/

# copy workdir
LIVE_DIR=/home/$USER/litai
TEMP_DIR=/home/$USER/litai-update
rm -rfd $TEMP_DIR
cp -r $LIVE_DIR $TEMP_DIR

# update code, recreate venv
cd $TEMP_DIR
git pull origin main:main -f
new_venv

# update pubmed database
echo "$(date +%F@%T:) Updating database"
cmd/get-files
python litai/db.py --append

# update scoring tables
for TABLE in hbot senescence; do
    echo "$(date +%F@%T:) Updating $TABLE table"
    python litai/score.py config/$TABLE.yaml
done

# upload db and website
echo "$(date +%F@%T:) Uploading data files"
export AZURE_STORAGE_CONNECTION_STRING="$(cat /home/$USER/secrets/litai-fileserver)"
az storage blob upload -f $TEMP_DB -c data -n $(basename $TEMP_DB)
az storage blob upload-batch -s html/ -d \$web

# publish new files to api
cd ~
rm -rfd $LIVE_DIR
mv $TEMP_DIR $LIVE_DIR

# recreate virtual environment
cd $LIVE_DIR
new_venv

# restart api
uvicorn litai.app:app --reload
